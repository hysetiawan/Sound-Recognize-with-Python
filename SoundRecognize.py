#membuka mikrofone dengan pyAudio untuk mendengar perintah

import pyaudio
import struct
import math
import os

command = "dir"

INITIAL_TAP_THRESHOLD = 0.090
FORMAT = pyaudio.paInt16 
SHORT_NORMALIZE = (1.0/32768.0)
CHANNELS = 2
RATE = 44100  
INPUT_BLOCK_TIME = 0.05
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)
# jika mendapat bagian suara yang berisik, ini untuk meningkatkan ambang batasnya
OVERSENSITIVE = 15.0/INPUT_BLOCK_TIME                    
# jika mendapat suara sekitar yang tenang, maka kurangi batasnya
UNDERSENSITIVE = 120.0/INPUT_BLOCK_TIME 
# jika suara lebih panjang dari blok suara, maka iru bukan ketukan
MAX_TAP_BLOCKS = 0.15/INPUT_BLOCK_TIME

def get_rms( block ):
    # gelombang RMS didefinsikan sebagai kuadrat
    # dari rata-rata, dari waktu ke waktu melalui kuadrat amplitudo.
    # dan kita harus mengubah string byte 
    # menjadi string sample 16 bit

    # kita mendapatkan satu short out
    # untuk setiap dua karakter string
    count = len(block)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, block )

    # mengulang blok
    sum_squares = 0.0
    for sample in shorts:
        # sampelnya adlah +/- 32768.
        # dinormalkan menjadi 1.0
        n = sample * SHORT_NORMALIZE
        sum_squares += n*n

    return math.sqrt( sum_squares / count )

class TapTester(object):
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.open_mic_stream()
        self.tap_threshold = INITIAL_TAP_THRESHOLD
        self.noisycount = MAX_TAP_BLOCKS+1 
        self.quietcount = 0 
        self.errorcount = 0

    def stop(self):
        self.stream.close()
    #ini proses untuk melihat mic yang tersedia
    def find_input_device(self):
        device_index = None            
        for i in range( self.pa.get_device_count() ):     
            devinfo = self.pa.get_device_info_by_index(i)   
            print( "Device %d: %s"%(i,devinfo["name"]) )

            for keyword in ["mic","input"]:
                if keyword in devinfo["name"].lower():
                    print( "Found an input: device %d - %s"%(i,devinfo["name"]) )
                    device_index = i
                    return device_index

        if device_index == None:
            print( "No preferred input found; using default input device." )

        return device_index
    #ini proses untuk menggunakan mic, agar python dapat mendengarkan suara
    def open_mic_stream( self ):
        device_index = self.find_input_device()

        stream = self.pa.open(   format = FORMAT,
                                 channels = CHANNELS,
                                 rate = RATE,
                                 input = True,
                                 input_device_index = device_index,
                                 frames_per_buffer = INPUT_FRAMES_PER_BLOCK)

        return stream
    #ini proses apabila tepukan terdengar
    def tapDetected(self):
        # os.system(command)
        print("Dokumen anda segera kami cetak....")
        os.startfile("document.docx","print")
        quit()
    # ini proses mendengarkan tepukannya
    def listen(self):
        try:
            block = self.stream.read(INPUT_FRAMES_PER_BLOCK)
        except IOError as e:
            # haha hayuuk
            self.errorcount += 1
            print( "(%d) Error recording: %s"%(self.errorcount,e) )
            self.noisycount = 1
            return

        amplitude = get_rms( block )
        if amplitude > self.tap_threshold:
            # blok suara noise
            self.quietcount = 0
            self.noisycount += 1
            if self.noisycount > OVERSENSITIVE:
                # mengurangi sensitivitas
                self.tap_threshold *= 1.1
        else:            
            # untuk blok yang tenang

            if 1 <= self.noisycount <= MAX_TAP_BLOCKS:
                self.tapDetected()
            self.noisycount = 0
            self.quietcount += 1
            if self.quietcount > UNDERSENSITIVE:
                # menaikkan sensitivitas
                self.tap_threshold *= 0.9

if __name__ == "__main__":
    tt = TapTester()

    for i in range(1000):
        tt.listen()
