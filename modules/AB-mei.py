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

import traceback

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
        arg_list = [a for a in arg_list if '/' not in a or re.match("http://|https://", a)]
        arg_list = [a for a in arg_list if not re.match("fd:\d+", a)]
        arg_list = [a for a in arg_list if not re.match("@.*", a)]

        # determine if argument is a URL or not
        for i, arg in enumerate(arg_list):
            if re.match("http://|https://", arg):
                arg_list[i] = (arg, "IMG")
            else:
                arg_list[i] = (arg, "ARG")

        # write to file and check if is image
        remove_list = []
        for i, arg in enumerate(arg_list):
            if arg[1] == "IMG":
                try:
                    frames = re.search(".*(\[.*\])", arg[0])
                    if frames:
                        frames = frames.group(1)
                        image_http_resp = requests.get(arg[0][:-len(frames)])
                    else:
                        frames = ""
                        image_http_resp = requests.get(arg[0])
                    tempname = self.randomName()
                    f = open(tempname, "wb")
                    f.write(image_http_resp.content)
                    f.close()
                    arg_list[i] = ((tempname, frames), "IMG")
                    remove_list.append(tempname)
                    subprocess.check_call(["identify", tempname])
                except:
                    traceback.print_exc()
                    for r in remove_list: os.remove(r)                   
                    self.sendmsg("Error occured trying to get image(s)")
                    return

        file_names, size_before = self.processImage(arg_list)

        if len(file_names) > 10:
            self.sendmsg("ImageMagick resulted in more than 10 images, aborting")
            for f in file_names: os.remove(f)
            return
        elif not file_names:
            traceback.print_exc()
            self.sendmsg("Error occured trying to get image(s)")

        optimized_images = []
        for f in file_names:
            optimized_images.append(self.optimizeImage(f))

        response = []
        size_after = 0
        for o in optimized_images:
            size_after += o[2]
            response.append(self.upload(o))

        if len(response) == 1:
            if size_after <= size_before:
                self.sendmsg("{} ({:.2f}% Reduction)".format(response[0], (1-size_after/size_before)*100))
            else:
                self.sendmsg("{} ({:.2f}% Increase)".format(response[0], (1-size_before/size_after)*100))
        elif len(response) > 1:
            for r in response:
                self.sendmsg(r)
            if size_after <= size_before:
                self.sendmsg("({:.2f}% Reduction)".format((1-size_after/size_before)*100))
            else:
                self.sendmsg("({:.2f}% Increase)".format((1-size_before/size_after)*100))

        for f in file_names: os.remove(f)

        return

    def randomName(self):
        return "data/images/_img_" + ''.join(random.choice(string.ascii_uppercase) for char in range(10))

    def processImage(self, arg_list):

        size = 0
        for i, arg in enumerate(arg_list):
            if arg[1] == "IMG":
                size += os.path.getsize(arg[0][0])

        # Don't do any processing if we have no arguments and all images are jpeg
        if "ARG" not in [a[1] for a in arg_list]:
            if not [imghdr.what(a[0][0]) for a in arg_list if imghdr.what(a[0][0]) != "jpeg"]:
                return [a[0][0] for a in arg_list], size
            
        result_name = self.randomName()
        if arg_list:
            if arg_list[-1][1] == "ARG" and arg_list[-1][0] in ["png", "jpeg", "jpg", "gif", "ico"]:
                result_name = self.randomName() + '.' + arg_list[-1][0]
                arg_list.remove(arg_list[-1])
            arg_list.append((result_name, "ARG"))

        try:
            call_list = list(arg_list)
            for i, c in enumerate(call_list):
                if c[1] == "IMG":
                    call_list[i] = (''.join(c[0]), "IMG")
            subprocess.check_call(["convert"] + [c[0] for c in call_list])
        except:
            for arg in arg_list:
                if arg[1] == "IMG":
                    os.remove(arg[0][0])
            self.sendmsg("ImageMagick Error")
            return [], 0

        for arg in arg_list:
            if arg[1] == "IMG":
                os.remove(arg[0][0])

        file_names = os.listdir("data/images/")
        file_names = ["data/images/" + f for f in file_names if re.search("{0}.*".format(os.path.splitext(os.path.basename(result_name))[0]), f)]

        return file_names, size

    def optimizeImage(self, file_name):

        image_type = imghdr.what(file_name)

        if image_type in ["jpeg", "png"]:
            if image_type == "jpeg":
                subprocess.check_call(["jpegoptim", "--strip-all", file_name])
            if image_type == "png":
                subprocess.check_call(["optipng", "-fix", file_name])

        return (file_name, image_type, os.path.getsize(file_name))

    def upload(self, image_info):

        data = self.jsonread("AB-mei")
        meiurl = data["meiurl"]
        
        image = open(image_info[0], "rb")
        image_type = image_info[1]

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
                    response = url
                else:
                    response = "ImageUpload Error: No image found"
            else:
                response = "ImageUpload Error: No response"
        
        return response
