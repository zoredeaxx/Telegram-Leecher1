import asyncio
import libtorrent as lt
import logging
import subprocess
import re
from datetime import datetime
from colab_leecher.utility.helper import sizeUnit, status_bar
from colab_leecher.utility.variables import BOT, Aria2c, Paths, Messages, BotTimes

async def libtorrent_download(link: str, num: int):
    ses = lt.session()
    params = {
        'save_path': Paths.down_path,
        'storage_mode': lt.storage_mode_t(2),
        'url': link
    }
    handle = ses.add_torrent(params)

    while not handle.has_metadata():
        await asyncio.sleep(1)

    total_size = handle.torrent_info().total_size()
    status = handle.status()
    while not status.is_seeding:
        status = handle.status()
        downloaded = status.total_done
        progress = downloaded / total_size * 100
        print(f"Progress: {progress}%")
        await asyncio.sleep(1)

    print("Download complete!")

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
            "libtorrent 🧨",
        )
