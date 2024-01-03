import os
import cv2
import random
import zipfile
import threading
import numpy as np
from pytube import YouTube
import time

def baixar_video(url, path):
    tentativas = 5
    for i in range(tentativas):
        try:
            yt = YouTube(url)
            video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            if not video:
                print(f"Unable to download video: {url}")
                return None
            return video.download(output_path=path)
        except Exception as e:
            print(f"Error downloading video: {e}. Retrying...")
            time.sleep(5)
    return None

def verificar_luminancia(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return np.mean(gray) >= (255 * 0.2)  # Retorna True se a luminância for maior ou igual a 20% de 255

def extrair_frame(video_path, segment_start, segment_end, output_folder, i):
    cap = cv2.VideoCapture(video_path)
    frame_selecionado = False

    while not frame_selecionado:
        frame_num = random.randint(segment_start, segment_end)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        if ret and verificar_luminancia(frame):
            cv2.imwrite(os.path.join(output_folder, f'frame_{i}.png'), frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])
            frame_selecionado = True

    cap.release()

def extrair_frames(video_path, output_folder, num_frames):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    segment_size = (total_frames - int(0.2 * total_frames)) // num_frames
    threads = []

    os.makedirs(output_folder, exist_ok=True)
    for i in range(num_frames):
        segment_start = int(0.1 * total_frames) + segment_size * i
        segment_end = segment_start + segment_size
        thread = threading.Thread(target=extrair_frame, args=(video_path, segment_start, segment_end, output_folder, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

def criar_zip(diretorio):
    with zipfile.ZipFile(f'{diretorio}.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(diretorio):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), diretorio))

def main():
    num_frames = 200  # Default number of frames to be extracted
    output_root = 'frames'

    with open('videos.txt', 'r') as file:
        urls = file.readlines()

    for url in urls:
        url = url.strip()
        video_path = baixar_video(url, 'videos')
        if video_path:
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_folder = os.path.join(output_root, video_name)
            print(f"Extracting frames from {video_name}...")
            extrair_frames(video_path, output_folder, num_frames)

    print(f"Creating zip for all videos...")
    criar_zip(output_root)
    print("Completed processing all videos.")

if __name__ == "__main__":
    main()
