#!/usr/bin/env python3

# author = Pranav Gummaraj Srinivas prgu6170@colorado.edu
# date = 11/27/2018
# name = Datacomm python programming assignment
# purpose = client code
# version = 3.6.5

import socket
import argparse
import logging
import json
import sys
from time import sleep
from Crypto.Cipher import AES
import configparser
import os
import math
import hashlib
import struct
import filecmp


def do_encrypt(fl):
    # creates encrypted version file
    key = 'sajfq874ohsdfp9qsajfq874ohsdfp9q'
    iv = '98qwy4thkjhwgpf9'
    aes = AES.new(key, AES.MODE_CBC, iv)
    file_size = os.path.getsize(fl)
    with open(fl+'.encr', 'wb') as fout:
        fout.write(struct.pack('<Q', file_size))
        with open(fl, "rb") as fin:
            while True:
                data = fin.read(2048)
                n = len(data)
                if n == 0:
                    break
                elif n % 16 != 0:
                    data += b' ' * (16 - n%16)
                encrptd_data = aes.encrypt(data)
                fout.write(encrptd_data)


def do_decrypt(encr_fl):
    # creates decrypted version of a file
    key = 'sajfq874ohsdfp9qsajfq874ohsdfp9q'
    iv = '98qwy4thkjhwgpf9'
    obj = AES.new(key, AES.MODE_CBC, iv)
    with open(encr_fl, 'rb') as fin:
        file_size = struct.unpack('<Q', fin.read(struct.calcsize('<Q')))[0]
        with open(encr_fl+'_decrpt', 'wb') as fout:
            while True:
                data = fin.read(2048)
                n = len(data)
                if n == 0:
                    break
                decrpt = obj.decrypt(data)
                if file_size > n:
                    fout.write(decrpt)
                else:
                    fout.write(decrpt[:file_size])
                file_size -= n


def md5(fname):
    # calculates md5 value of a file and returns mod 4 value of that hash value
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    md5_value = hash_md5.hexdigest()
    req_value = int(md5_value, 16) % 4
    return req_value


def validate_ip(address):
    # validates input IP address
    valid = True
    arr = address.split(".")
    if len(arr) != 4:
        valid = False
    else:
        for element in arr:
            if element != "":
                if int(element) < 0 or int(element) > 255:
                    valid = False
            else:
                valid = False
    return valid


def split_equal(mfile):
    # splits file into 4 equal parts and returns one part at a time
    content = mfile.read()
    return (content[i: i + math.ceil(len(content) / 4)] for i in range(0, len(content), math.ceil(len(content) / 4)))


def decision_list():
    # Returns a list of dictionaries of lists that tells which part of file should be uploaded to which servers
    # For example, if md5 value is 2, then 0 (1st) part of file is uploaded to 1 (2nd) and 2 (3rd) server
    lst = [{} for i in range(4)]
    lst[0][0] = [3, 0]; lst[0][1] = [0, 1]; lst[0][2] = [1, 2]; lst[0][3] = [2, 3]
    lst[1][0] = [0, 1]; lst[1][1] = [1, 2]; lst[1][2] = [2, 3]; lst[1][3] = [3, 0]
    lst[2][0] = [1, 2]; lst[2][1] = [2, 3]; lst[2][2] = [3, 0]; lst[2][3] = [0, 1]
    lst[3][0] = [2, 3]; lst[3][1] = [3, 0]; lst[3][2] = [0, 1]; lst[3][3] = [1, 2]
    return lst


def user_validity(sockets, user, pwd):
    # validates user and password entered against credentials registered with server in dfs.conf file
    allowed = False
    for client_socket in sockets:
        try:
            client_socket.send(user.encode('utf8'))
            sleep(0.05)
            client_socket.send(pwd.encode('utf8'))
        except BrokenPipeError:
            pass
        try:
            auth = client_socket.recv(1024)
            if auth.decode('utf8') == 'valid':
                allowed = True
        except ConnectionError:
            pass
    return allowed


def get_req_servers(active_serv, value):
    # Based on md5 value returns a dictionary which gives which part should be obtained from which active server.
    # helps in traffic optimization
    dec_list = decision_list()
    req_dict = dec_list[value]
    final_dict = {}
    for part_num in range(4):
        for serv_num in req_dict[part_num]:
            if serv_num in active_serv:
                final_dict[part_num+1] = serv_num
                break
    return final_dict


def create_socket(server_names, server_ports, usr, pswd):
    # Define the socket
    while True:
        client_sockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for server_port in server_ports]
        i = 0
        for server_port in server_ports:
            try:
                client_sockets[i].connect((server_names[i], int(server_port)))
            except ConnectionRefusedError:
                pass
            i += 1
        credentials = []
        for ser in range(4):
            try:
                client_sockets[ser].send(usr.encode('utf8'))
                sleep(0.05)
                client_sockets[ser].send(pswd.encode('utf8'))
            except BrokenPipeError:
                pass

            validity = client_sockets[ser].recv(512)    # if validated by at least one server proceeds further
            credentials.append(validity.decode('utf8'))
        if 'valid' in credentials:
            print("You have the following options:")
            print("-get <filename> <username> <password>")
            print("-put <filename> <username> <password>")
            print("-list <username> <password>")
            inp = input("Please enter your input (in the exact format show):\n")
            ip = inp.split()
            if len(ip) == 3:
                func = ip[0]
                username = ip[1]
                password = ip[2]
            elif len(ip) == 4:
                func = ip[0]
                file_name = ip[1]
                username = ip[2]
                password = ip[3]
            else:
                logs.info("Invalid command")
                continue
            active_servers = []
            for ser in range(4):
                try:
                    client_sockets[ser].send(func.encode('utf8'))
                    active_servers.append(ser)   # appending server that is active to a list
                    sleep(0.05)
                except BrokenPipeError:
                    pass
            if (len(ip) == 4 and (func == "-get" or func == "-put")) or (len(ip) == 3 and func == "-list"):
                # validate user and password entered in the command
                valid = user_validity(client_sockets, username, password)
                if valid:

                    if func == '-get':

                        for ser in range(4):
                            try:
                                client_sockets[ser].send(file_name.encode('utf8'))
                                sleep(0.1)
                                flag = client_sockets[ser].recv(2048).decode('utf8')
                                sleep(0.1)
                                if flag == "found":
                                    dec_value = int(client_sockets[ser].recv(2048).decode('utf8'))
                            except BrokenPipeError:
                                pass
                        if flag == "found":
                            req_servers = get_req_servers(active_servers, dec_value)
                            if len(req_servers) == 4:
                                # creating a list of parts that needs to be combined to create original file
                                parts = []
                                print("Active servers are: ", list(map(lambda x: x+1, active_servers)))
                                # upload each part to respective servers given by get_req_servers()
                                for part_num in range(1, 5):
                                    print("Getting part "+str(part_num)+" from sever "+str(req_servers[part_num]+1))
                                    client_sockets[req_servers[part_num]].send('%true%'.encode('utf8'))
                                    prt_name = "."+file_name+"."+str(part_num)
                                    parts.append('.copy_'+prt_name+'_decrpt')
                                    sleep(0.05)
                                    client_sockets[req_servers[part_num]].send(prt_name.encode('utf8'))
                                    sleep(0.05)
                                    data = client_sockets[req_servers[part_num]].recv(32)
                                    if data.decode('utf8') == "%BEGIN%":
                                        with open('.copy_'+prt_name, "wb") as f:
                                            l = 0
                                            while True:
                                                sys.stdout.flush()
                                                l += 1
                                                print("\r"+"Receiving encrypted data" + "."*(l%60), end='')
                                                data = client_sockets[req_servers[part_num]].recv(2048)
                                                try:
                                                    if data.decode('utf8') == "%END%":
                                                        break
                                                except UnicodeDecodeError:
                                                    pass
                                                f.write(data)
                                        f.close()
                                    print("\nSuccessfully transferred part "+str(part_num))
                                    do_decrypt('.copy_'+prt_name)  # creating a decrypted file
                                    sleep(1)
                                for act_ser in active_servers:
                                    client_sockets[act_ser].send('%false%'.encode('utf8'))
                                # combine and create a complete decrypted file
                                with open("copy_"+file_name, "wb") as outfile:
                                    for fname in parts:
                                        with open(fname, 'rb') as infile:
                                            for line in infile:
                                                outfile.write(line)
                                print("File has been saved as copy_"+file_name+" from the servers")
                                
                                break
                            else:
                                logs.info("File not complete!")
                                break
                        else:
                            logs.info("File not uploaded by the user")
                            break

                    elif func == '-put':
                            try:
                                with open(file_name, 'rb') as fil:
                                    part_number = 1
                                    # create 4 equal parts of files
                                    for part in split_equal(fil):
                                        pt_name = '.'+file_name+'.'+str(part_number)
                                        with open(pt_name, 'wb') as newfile:
                                            newfile.write(part)
                                        do_encrypt(pt_name)   # create encrypted version of each file
                                        part_number += 1

                                decision_value = md5(file_name)
                                # getting information of which part should be uploaded to which server
                                upload_value = decision_list()
                                upload_dict = upload_value[decision_value]
                                fail = False
                                for i in range(4):
                                    sleep(0.05)
                                    try:
                                        client_sockets[upload_dict[i][0]].send(file_name.encode('utf8'))
                                        sleep(0.05)
                                        client_sockets[upload_dict[i][0]].send(str(decision_value).encode('utf8'))
                                    except BrokenPipeError:
                                        logs.info("Server "+str(upload_dict[i][0]+1)+" is not up. Cannot upload the file.")
                                        for j in range(4):
                                            try:
                                                client_sockets[upload_dict[j][0]].send("%false%".encode('utf8'))
                                            except BrokenPipeError:
                                                pass
                                        fail = True
                                        break
                                if fail:
                                    break

                                for i in range(4):
                                    client_sockets[upload_dict[i][1]].send("%true%".encode('utf8'))
                                    client_sockets[upload_dict[i][0]].send("%true%".encode('utf8'))
                                    part_name = '.'+file_name+'.'+str(i+1)
                                    print("\n"+"Sending "+file_name+" part "+str(i+1)+" to servers "
                                          +str(upload_dict[i][1]+1)+" and "+str(upload_dict[i][0]+1))
                                    sleep(0.05)
                                    client_sockets[upload_dict[i][0]].send(part_name.encode('utf8'))
                                    client_sockets[upload_dict[i][1]].send(part_name.encode('utf8'))

                                    # sending encrypted parts to respective servers
                                    with open(part_name+'.encr', 'rb') as f:
                                        line = f.read(2048)
                                        sleep(0.05)
                                        client_sockets[upload_dict[i][1]].send("%BEGIN%".encode('utf8'))
                                        client_sockets[upload_dict[i][0]].send("%BEGIN%".encode('utf8'))
                                        sleep(0.05)
                                        l = 0
                                        while line:
                                            l += 1
                                            print("\r" + "Sending encrypted data" + "." * (l % 60), end='')
                                            sys.stdout.flush()
                                            client_sockets[upload_dict[i][1]].send(line)
                                            sleep(0.01)
                                            client_sockets[upload_dict[i][0]].send(line)
                                            line = f.read(2048)
                                        client_sockets[upload_dict[i][1]].send("%END%".encode('utf8'))
                                        sleep(0.01)
                                        client_sockets[upload_dict[i][0]].send("%END%".encode('utf8'))
                                    f.close()

                                for client_socket in client_sockets:
                                    sleep(0.05)
                                    client_socket.send("%false%".encode('utf8'))
                                print("\nDone Sending")
                                break
                            except FileNotFoundError:
                                logs.info("File not Found!")
                                break

                    elif func == "-list":
                        for ser in active_servers:
                            try:
                                data = client_sockets[ser].recv(2048)
                                lst = json.loads(data.decode('utf8'))
                                list_of_files = lst.get("list")
                                print('\nListing all files in the directory:')
                                # For each file check availability of servers for each part. If at least one part
                                # could not be retrieved by available servers it is marked incomplete.
                                for item in list_of_files:
                                    req_servers = get_req_servers(active_servers, int(item[1]))
                                    if len(req_servers) == 4:
                                        print("---->  " + item[0])
                                    else:
                                        print("---->  " + item[0] + " [INCOMPLETE]")
                                break
                            except BrokenPipeError:
                                pass
                        else:
                            logs.info("None of the servers are listening")
                        break

                    else:
                        logs.info("Invalid command")
                        continue
                else:
                    logs.info("Invalid username or password\nTry again!")
                    continue
            else:
                logs.info("Invalid command")
                continue
        else:
            logs.info("Invalid credentials in the .conf file or no server could be reached")
            break
    for client_socket in client_sockets:
        try:
            client_socket.close()
        except BrokenPipeError:
            pass
    print('Connection closed')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logs = logging.getLogger(__name__)
    config = configparser.ConfigParser()
    parser = argparse.ArgumentParser()
    parser.add_argument('configfile', help="Enter name of the config file", type=str)
    arg = parser.parse_args()
    configfile = arg.configfile
    config.read(configfile)
    user = config['credentials']['username']
    password = config['credentials']['password']
    server_port = []
    server_names = []
    for (server, address) in config.items('server_list'):
        port = address.split(":")
        server_port.append(int(port[1]))
        server_names.append(port[0])
    for server_name in server_names:
        if not validate_ip(server_name):
            logs.info("Invalid IP address")
            sys.exit()

    create_socket(server_names, server_port, user, password)
