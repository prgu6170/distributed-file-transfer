#!/usr/bin/env python3

# author = Pranav Gummaraj Srinivas prgu6170@colorado.edu
# date = 11/27/2018
# name = Datacomm python programming assignment
# purpose = server code
# version = 3.6.5

import socket
import argparse
import logging
import sys
import os
import json
import configparser
from time import sleep
import csv
import threading


def validate_ip(address):
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


def user_validity(credential, connection):
    # validates username and password against the credentials in the conf file passed
    valid = False
    user = connection.recv(128)
    pswd = connection.recv(128)
    if credential[user.decode('utf8')] == pswd.decode('utf8'):
        valid = True
    return valid, user.decode('utf8')


def files(directory, user):
    # read .filerepository.csv stored in a directory and return the list of files stored in that directory
    file_list = []
    try:
        with open('.'+directory+'/'+user+"/"+".filerepository.csv", "r") as f:
            readCSV = csv.reader(f, delimiter=',')
            for row in readCSV:
                if not [row[0], row[1]] in file_list:
                    file_list.append([row[0], row[1]])
    except FileNotFoundError:
        return file_list
    return file_list


def create_socket(server_name, server_port, dr, crd):
    # Define socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Server socket should bind to one IP and port it is listening on. This must match with dest port on client
        server_socket.bind((server_name, server_port))
        print("Server is ready")
        server_socket.listen(5)
        # Always listening
        while True:
            connection, client_address = server_socket.accept()
            print("Got connection from ", client_address)
            # threading incoming clients
            threading.Thread(target=process_client, args=(connection, dr, crd)).start()
    except OSError:
        logs.info("Port already in use")


def process_client(conn, drctry, cred):

    usr = conn.recv(512)     # username in dfc file
    usr = usr.decode('utf8')
    sleep(0.05)
    pas = conn.recv(512)    # password in dfc file
    pas = pas.decode('utf8')

    try:
        if cred[usr] == pas:     # validating user and password in dfc.conf file
            conn.send("valid".encode('utf8'))
            func = conn.recv(2048)
            validity, user = user_validity(cred, conn)    # validating username and password entered along with get, put or list
            if validity:
                conn.send('valid'.encode('utf8'))

                if func.decode('utf8') == "-get":

                    file_name = conn.recv(2048).decode('utf8')
                    lst = files(drctry, user)    # returns list of files uploaded by the user
                    found = False
                    for item in lst:
                        if file_name == item[0]:
                            conn.send("found".encode('utf8'))
                            sleep(0.2)
                            conn.send(item[1].encode('utf8'))
                            found = True
                            break
                    else:
                        conn.send("notfound".encode('utf8'))
                    if found:
                        while True:
                            listn = conn.recv(2048)
                            if listn.decode('utf8') == "%true%":
                                prt_name = conn.recv(2048)
                                print((prt_name.decode('utf8')))
                                try:
                                    f = open('.' + drctry + '/' + user + '/' + prt_name.decode('utf8'), 'rb')
                                    conn.send("%BEGIN%".encode('utf8'))
                                    sleep(0.05)
                                    line = f.read(2048)
                                    l = 0
                                    while line:     # if found, starts sending data to the client
                                        l += 1
                                        print("\r" + "Sending data" + "." * (l % 60), end='')
                                        sys.stdout.flush()
                                        sleep(0.01)
                                        conn.send(line)
                                        line = f.read(2048)
                                    f.close()
                                    sleep(0.05)
                                    conn.send("%END%".encode('utf8'))
                                    print("\nDone Sending")
                                except FileNotFoundError:
                                    logs.info("File not Found!")
                            else:
                                break

                elif func.decode('utf8') == "-put":
                    act_file_name = conn.recv(2048).decode('utf8')
                    decision_value = conn.recv(2048).decode('utf8')
                    try:
                        os.mkdir('.' + drctry + '/' + user)     # creates directory by the name of user
                    except FileExistsError:
                        pass
                    # maintain a file in each directory that contains list of files uploaded and md5 value of the file.
                    with open('.' + drctry + '/' + user + "/" + ".filerepository.csv", "a+") as f:
                        write = csv.writer(f)
                        write.writerow([act_file_name, decision_value])
                    while True:
                        listen = conn.recv(2048)
                        if listen.decode('utf8') == "%true%":
                            file_name = conn.recv(2048)
                            print(file_name.decode("utf8"))
                            data = conn.recv(2048)
                            if data.decode('utf8') == "%BEGIN%":
                                with open('.' + drctry + '/' + user + '/' + file_name.decode('utf8'), 'wb') as file:
                                    l = 0
                                    # writes data to the file until it receives end of file
                                    while True:
                                        sys.stdout.flush()
                                        l += 1
                                        print("\r" + "Receiving data" + "." * (l % 60), end='')
                                        data = conn.recv(2048)
                                        try:
                                            if data.decode('utf8') == "%END%":
                                                break
                                        except UnicodeDecodeError:
                                            pass

                                        file.write(data)
                                file.close()

                            print("\nSuccessfully transferred file")
                        else:
                            break

                elif func.decode('utf8') == "-list":
                    print(drctry, user)
                    # reads .filerepository.csv file saved in the respective folder to get a list of files.
                    list_of_file = files(drctry, user)
                    data = json.dumps({"list": list_of_file})
                    print("Sending list of files in the directory")
                    print(os.getcwd())
                    conn.send(data.encode('utf8'))    # sends the list to a client.
                    print("Sent")

            else:
                conn.send('inval'.encode('utf8'))

        else:
            conn.send("invalid".encode('utf8'))
    except KeyError:
        conn.send("invalid".encode('utf8'))
    conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logs = logging.getLogger(__name__)
    parser = argparse.ArgumentParser()
    parser.add_argument("server_directory", help="Give directory address of the server", type=str,
                        choices=['/DFS1', "/DFS2", "/DFS3", "/DFS4"])
    parser.add_argument("serverPort", help="Enter port of the server you wish to connect", type=int)
    args = parser.parse_args()
    server_name = "127.0.0.1"
    server_directory = args.server_directory
    server_port = args.serverPort
    try:
        os.mkdir("."+server_directory)     # creates a directory with the username
    except FileExistsError:
        pass
    if not validate_ip(server_name):
        logs.info("Invalid IP address")
        sys.exit()
    config = configparser.ConfigParser()
    config.read('dfs.conf')    # reads dfs.conf file which has valid user names and passwords
    cred = config['credentials']

    create_socket(server_name, server_port, server_directory, cred)


