# distributed-file-system
Distributed file system project is a client-server model built using socket programming in Python3.

This project consists of two part: a client and a server.
Client can choose to upload, download or list files present in the servers which were uploaded by him/her. Files could be of any format and of any size. When client uploads a file, it is divided into four almost equal parts and encrypted and each part is sent to two of the four servers to ensure redundancy. Decision of which part will be stored in which server is based on MD5 hash value of the file (not the file name). Servers do not decrypt the files and they are stored as is for security. For a file to be uploaded it is necessary that all the four servers should be up. To get the servers up and running a configuration file and the port number should be passed which will be the server’s port. Server can be run by the following command:
$python3 dfs.py /DFS[n] [port number]
where [n] is the server number.

To run the client program an argument of the configuration file should be passed which contains the servers’ IP addresses, port numbers and a username and password to authenticate client. Following command can be used to run the client:
$python3 dfc.py dfc.conf

To upload, download, or to list a file a user needs to authenticate himself by providing a username and a password every time he issues these commands. For example, if user wants to upload a file he should enter:
-put file.pdf username password

When trying to download, or list the files he/she has uploaded, if the servers that are running are not sufficient to reconstruct the file, user will be notified. But if servers are sufficient to reconstruct the file, he/she could download the file. While downloading client	gets only one instance of each part from the available servers to optimise traffic in the network.

Servers can handle upto 5 users simultaneously. 

Note: Usernames are not case sensitive while passwords are. 

Key features:
- Redundancy
- Encrypted file transfer and storage
- Traffic optimisation
- Server can handle multiple connections
- Supports any format of file of any length 
