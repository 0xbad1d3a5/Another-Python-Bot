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

        arg_list = list(self.args)

        # filter out some dangerous input
        arg_list = [a for a in arg_list if "../" not in a]
        arg_list = [a for a in arg_list if a != '*']
        arg_list = [a for a in arg_list if '/' not in a or re.search("http://|https://", a)]

        for i, arg in enumerate(arg_list):
            if re.search("http://|https://", arg):
                arg_list[i] = (arg, "IMG")
            else:
                arg_list[i] = (arg, "ARG")

        for i, arg in enumerate(arg_list):
            if arg[1] == "IMG":
                try:
                    image_http_resp = requests.get(arg[0])
                    if not imghdr.what(None, image_http_resp.content):
                        raise Exception
                    arg_list[i] = (image_http_resp.content, "IMG")
                except:
                    self.sendmsg("Error occured trying to get image(s)")
                    return

        self.processImage(arg_list)

        return

    def randomName(self):
        return "data/images/_img_" + ''.join(random.choice(string.ascii_uppercase) for char in range(10))

    def processImage(self, arg_list):

        size = 0
        for i, arg in enumerate(arg_list):
            if arg[1] == "IMG":
                tempname = self.randomName()
                f = open(tempname, "wb")
                f.write(arg[0])
                f.close()
                size += os.path.getsize(tempname)
                arg_list[i] = (tempname, "IMG")

        result_name = self.randomName()
        arg_list.append((result_name, "ARG"))
        try:
            subprocess.check_call(["convert"] + [a[0] for a in arg_list])
        except:
            for arg in arg_list:
                if arg[1] == "IMG":
                    os.remove(arg[0])
            self.sendmsg("ImageMagick Error")
            return

    def upload(self, image_info):
        data = self.jsonread("AB-mei")
        meiurl = data["meiurl"]
        
        image = image_info[0]
        image_type = image_info[1]
        image_resp = image_info[2]

        response = ""
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
                    response = url + ' (' + image_resp + ')'
                else:
                    response = "ImageUpload Error: No image found"
            else:
                response = "ImageUpload Error: No response"
        
        return response
    
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
                if "-lossy" in self.args:
                    filename = os.path.splitext(tempname)[0]
                    subprocess.check_call(["convert", "-quality", "60", tempname, filename + ".jpeg"])
                    tempname = filename + ".jpeg"
                    image_type = ".jpeg"
                else:
                    if image_type == "jpeg":
                        subprocess.check_call(["jpegoptim", "-s", tempname])
                    if image_type == "png":
                        subprocess.check_call(["optipng", "-fix", tempname])
                image_file = open(tempname, "rb")
                return (image_file, image_type, "{:.2f}% Reduction".format((1-os.path.getsize(tempname)/size)*100), tempname)
            except:
                return (image_file, image_type, "Error optimizing image", None)
        # Can't optimize the image
        else:
            return (image, image_type, "Unable to optimize", None)
