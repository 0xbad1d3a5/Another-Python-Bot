import os
import re
import http
import imghdr
import base64
import string
import random
import urllib
import subprocess

from urllib.request import urlopen

from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    cmd = ".t"

    def __init__(self, msg, share):
        super(Module, self).__init__(msg, share)

    def main(self):

        data = self.jsonread("mei")

        # Download the image, and return if not possible
        try: image_file = urlopen(self.args[0])
        except:
            self.sendmsg("Image not found")
            return
        
        image_list = self.optimizeImage(image_file)
        image = image_list[0].read()
        image_type = image_list[1]
        image_resp = image_list[2]

        
        if image_type:

            MEI = http.client.HTTPSConnection(data["MEI"])
            meiheader = data["meiheader"]
            
            b = r"--stopboundaryhere\r\n"
            b += r"Content-Disposition: form-data; name=\"numFiles\"\r\n\r\n"
            b += r"3"
            b += r"--stopboundaryhere\r\n"
            b += r"Content-Disposition: form-data; name=\"ufile0\"; filename=\"asda." + image_type + "\"" + "\r\n"
            b += r"Content-Type: image/" + image_type + "\r\n"
            b += r"Content-Transfer-Encoding: base64\r\n\r\n"
            b += str(image)
            b += r"\r\n--stopboundaryhere\r\n"
            b += r"Content-Disposition: form-data; name=\"Submit\"\r\n\r\n"
            b += r"Upload\r\n"
            b += r"--stopboundaryhere\r\n"
            
            print(image)
            print(b)

            resp = self.reqPage(MEI, "POST", "/upload_ac.php", b, meiheader)
            print(resp.getheaders())
            

        return
    
    def optimizeImage(self, image_file):
        # Read the image
        image = image_file.read()
        image_type = imghdr.what(None, image)
        # We can optimize the image
        if image_type in ["jpeg", "png"]:
            # Write the image to file
            tempname = "data/_img_" + ''.join(random.choice(string.ascii_uppercase) for char in range(10))
            f = open(tempname, "wb")
            f.write(image)
            f.close()
            size = os.path.getsize(tempname)
            # Optimize the images and check call
            try:
                if image_type == "jpeg": subprocess.check_call(["data/jpegoptim", "-s", tempname])
                if image_type == "png": subprocess.check_call(["data/optipng", tempname])
                image_file = open(tempname, "rb")
                return (image_file,image_type,"{:.2f}% Reduction".format((1-os.path.getsize(tempname)/size)*100))
            except:
                return (image_file, image_type, "Error optimizing image")
        # Can't optimize the image
        else:
            return (image_file, image_type, "Unable to optimize")
