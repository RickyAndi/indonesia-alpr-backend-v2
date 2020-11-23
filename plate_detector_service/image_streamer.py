
import subprocess as sp

class ImageStreamer:
    
    def __init__(self, rtsp_server_url, fps, sizeStr):
        
        self.fps = fps
        self.rtsp_server_url = rtsp_server_url
        self.sizeStr = sizeStr

        self.command = ['ffmpeg',
            '-re',
            '-s', sizeStr,
            '-r', str(self.fps),  # rtsp fps (from input server)
            '-i', '-',
            
            # You can change ffmpeg parameter after this item.
            '-pix_fmt', 'yuv420p',
            '-r', '30',  # output fps
            '-g', '50',
            '-c:v', 'libx264',
            '-b:v', '2M',
            '-bufsize', '64M',
            '-maxrate', "4M",
            '-preset', 'veryfast',
            '-rtsp_transport', 'tcp',
            '-segment_times', '5',
            '-f', 'rtsp',
            self.rtsp_server_url]
        
        self.process = sp.Popen(self.command, stdin=sp.PIPE)

    def send_to_stream(self, image):
        self.process.stdin.write(image.tobytes())