"""
   (C) 2019 Raryel C. Souza
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import platform
import os
import subprocess
import socket


class MyUtil(object):
    @staticmethod
    def open_file(file_path):
        """Open file in files browser depinding on OS."""
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", file_path])
        else:
            subprocess.Popen(["xdg-open", file_path])

    @staticmethod
    def able_to_access_service(service: str = "Google"):
        """Check if we are able to access services."""
        # TODO: Get the urls from a shared source.
        services = {
            "Wit.ai": "api.wit.ai",
            "Google": "www.google.com",
            "xfyun": "iat-api.xfyun.cn",
            "baidu_asr": "vop.baidu.com",
            "baidu_pro_asr": "vop.baidu.com",
        }

        try:
            url = services[service]
        except KeyError:
            raise KeyError(f'No service with the name "{service}" is available.')

        try:
            # Connect to the host -- tells us if the host is actually reachable.
            s = socket.create_connection((url, 80), 2)
            s.close()
        except OSError:
            return False
        else:
            return True

    @staticmethod
    def percentage(currentval, maxval):
        """Calculate the progrees percentage."""
        return 100 * currentval / float(maxval)
