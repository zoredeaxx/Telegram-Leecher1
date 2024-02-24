import asyncio
import re
import logging
import subprocess
import libtorrent as lt
from datetime import datetime
from colab_leecher.utility.helper import sizeUnit, status_bar
from colab_leecher.utility.variables import BOT, Aria2c, Paths, Messages, BotTimes


async def libtorrent_Download(link: str, num: int):
    global BotTimes, Messages
    name_d = await get_Aria2c_Name(link)
    BotTimes.task_start = datetime.now()
    Messages.status_head = f"<b>📥 DOWNLOADING FROM » </b><i>🔗Link {str(num).zfill(2)}</i>\n\n<b>🏷️ Name » </b><code>{name_d}</code>\n"
    
    try:
        ses = lt.session()
        ses.listen_on(6881, 6891)
        handle = lt.add_magnet_uri(ses, link, {"save_path": Paths.down_path})
        BotTimes.task_start = datetime.now()

        while not handle.has_metadata():
            await asyncio.sleep(1)
        torrent_info = handle.get_torrent_info()
        name = torrent_info.name()

        while not handle.is_seed():
            s = handle.status()
            downloaded = s.total_download
            total = torrent_info.total_size()
            progress_percentage = downloaded / total * 100

            # Get download speed, ETA, etc.
            current_speed = s.download_rate
            eta = s.time_left
            downloaded_bytes = s.total_download
            total_size = total
            elapsed_time_seconds = (datetime.now() - BotTimes.task_start).seconds
            percentage = progress_percentage

            speed_string = f"{sizeUnit(current_speed)}/s"
            await status_bar(
                Messages.status_head,
                speed_string,
                int(percentage),
                eta,
                downloaded_bytes,
                total_size,
                "libtorrent 🌩️",
            )

            # Update UI or log progress
            await asyncio.sleep(1)

    except Exception as e:
        logging.error(f"libtorrent download failed: {e}")
        logging.info("Switching to aria2...")
        await aria2_Download(link, num)


async def aria2_Download(link: str, num: int):
    global BotTimes, Messages
    name_d = await get_Aria2c_Name(link)
    BotTimes.task_start = datetime.now()
    Messages.status_head = f"<b>📥 DOWNLOADING FROM » </b><i>🔗Link {str(num).zfill(2)}</i>\n\n<b>🏷️ Name » </b><code>{name_d}</code>\n"

    # Create a command to run aria2p with the link
    command = [
        "aria2c",
        "-x16",  # Increase the number of connections per download
        "--seed-time=0",
        "--summary-interval=1",
        "--max-tries=3",
        "--console-log-level=notice",
        "-d",
        Paths.down_path,
        link,
    ]

    # Run the command using subprocess.Popen
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Read and print output in real-time
    while True:
        output = await proc.stdout.readline()
        if not output:
            break
        await on_output(output.decode("utf-8"))

    # Retrieve exit code and any error output
    await proc.communicate()
    exit_code = proc.returncode
    if exit_code != 0:
        if exit_code == 3:
            logging.error(f"The Resource was Not Found in {link}")
        elif exit_code == 9:
            logging.error(f"Not enough disk space available")
        elif exit_code == 24:
            logging.error(f"HTTP authorization failed.")
        else:
            logging.error(
                f"aria2c download failed with return code {exit_code} for {link}"
            )


async def on_output(output: str):
    global link_info
    total_size = "0B"
    progress_percentage = "0B"
    downloaded_bytes = "0B"
    eta = "0S"
    try:
        if "ETA:" in output:
            parts = output.split()
            total_size = parts[1].split("/")[1]
            total_size = total_size.split("(")[0]
            progress_percentage = parts[1][parts[1].find("(") + 1 : parts[1].find(")")]
            downloaded_bytes = parts[1].split("/")[0]
            eta = parts[4].split(":")[1][:-1]
    except Exception as do:
        logging.error(f"Could't Get Info Due to: {do}")

    percentage = re.findall("\d+\.\d+|\d+", progress_percentage)[0]  # type: ignore
    down = re.findall("\d+\.\d+|\d+", downloaded_bytes)[0]  # type: ignore
    down_unit = re.findall("[a-zA-Z]+", downloaded_bytes)[0]
    if "G" in down_unit:
        spd = 3
    elif "M" in down_unit:
        spd = 2
    elif "K" in down_unit:
        spd = 1
    else:
        spd = 0

    elapsed_time_seconds = (datetime.now() - BotTimes.task_start).seconds

    if elapsed_time_seconds >= 270 and not Aria2c.link_info:
        logging.error("Failed to get download information ! Probably dead link 💀")
    # Only Do this if got Information
    if total_size != "0B":
        # Calculate download speed
        Aria2c.link_info = True
        current_speed = (float(down) * 1024**spd) / elapsed_time_seconds
        speed_string = f"{sizeUnit(current_speed)}/s"

        await status_bar(
            Messages.status_head,
            speed_string,
            int(percentage),
            eta,
            downloaded_bytes,
            total_size,
            "Aria2c 🧨",
        )


async def get_Aria2c_Name(link):
    if len(BOT.Options.custom_name) != 0:
        return BOT.Options.custom_name
    cmd = f'aria2c -x10 --dry-run --file-allocation=none "{link}"'
    result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
    stdout_str = result.stdout.decode("utf-8")
    filename = stdout_str.split("complete: ")[-1].split("\n")[0]
    name = filename.split("/")[-1]
    if len(name) == 0:
        name = "UNKNOWN DOWNLOAD NAME"
    return name
