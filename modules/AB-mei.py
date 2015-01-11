import os
import re
import http
import imghdr
import base64
import string
import random
import urllib
import subprocess
import requests

from urllib.request import urlopen

from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    cmd = ".mei "

    def __init__(self, msg, share):
        super(Module, self).__init__(msg, share)

    def main(self):

        data = self.jsonread("AB-mei")
        meiurl = data["meiurl"]

        # Download the image, and return if not possible
        try: image_file = requests.get(self.args[0])
        except:
            self.sendmsg("Image not found")
            return
        
        image_list = self.optimizeImage(image_file)
        image = image_list[0]
        image_type = image_list[1]
        image_resp = image_list[2]
        
        if image_type:
            data = { 'numFiles' : '1' }
            files = { ('ufile0', ('a.'+image_type, image, 'image/'+image_type)) }
            resp = requests.post("https://mei.animebytes.tv/upload_ac.php",
                              files=files,
                              data={ 'numFiles' : '1', 'Submit' : 'Upload' },
                              allow_redirects=False)
            if resp != None:
                url = resp.headers["Location"]
                url = re.search("imageupload.php\?img=(.*)", url).group(1)
                url = meiurl + url
                if url != meiurl:
                    self.sendmsg(url + ' (' + image_resp + ')')
                else:
                    self.sendmsg("ImageUpload Error: No image found")
            else:
                self.sendmsg("ImageUpload Error: No response")
        
        if image_list[3] is not None:
            os.remove(image_list[3])
        
        return
    
    def optimizeImage(self, image_file):
        # Read the image
        image = image_file.content
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
                if image_type == "jpeg": subprocess.check_call(["jpegoptim", "-s", tempname])
                if image_type == "png": subprocess.check_call(["optipng", tempname])
                image_file = open(tempname, "rb")
                return (image_file,image_type,"{:.2f}% Reduction".format((1-os.path.getsize(tempname)/size)*100), tempname)
            except:
                return (image_file, image_type, "Error optimizing image")
        # Can't optimize the image
        else:
            return (image_file, image_type, "Unable to optimize", None)
