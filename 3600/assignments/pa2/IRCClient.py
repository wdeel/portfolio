from optparse import OptionParser
from socket import *
import os, sys, threading
import selectors
import logging
import types
from IRCServer import Channel


class IRCClient(object):
    
    def __init__(self, options, run_on_localhost=False):
        # TODO: Initialize any required code here

        # create a TCP Client socket variable
        self.clientSocket = None

        # DO NOT EDIT ANYTHING BELOW THIS LINE IN __init__
        # -----------------------------------------------------------------------------

        # Indicates if we're simulating an IRC network, or actually running one
        # NOTE: As of right now, this should always be true.
        self.simulate = options.simulate

        # The name, address,and port the server you are connecting to is running on
        self.serverhost = options.serverhost
        self.serveraddr = options.serverhost
        self.serverport = options.serverport

        # If we're supposed to run this server on localhost, then change the connect_to_host_addr to 127.0.0.1
        if run_on_localhost:
            self.serveraddr = "127.0.0.1"

        # The information about this user
        self.nick = options.nick
        self.hostname = options.hostname
        self.servername = options.serverhost
        self.realname = options.realname

        # A list of all the user nicks that we know about
        self.users = []
        # A dictionary containing information about all the channels we're registered to
        self.channels = {}
        
        # Options to help with debugging and logging
        self.debug = options.debug
        self.verbose = options.verbose
        self.log_file = options.log_file
        self.logger = None

        # Start logging information about this client
        self.init_logging()

        # The read buffer that we write to in order to send information to the server
        self.server_read_buffer = ""
        
        # This dictionary contains mappings from responses to response handlers.
        # Upon receiving a response X, the appropriate response handler can be called with: self.response_handlers[X](...args)
        self.response_handlers = {
            "331":self.handle_rpl_notopic,
            "332":self.handle_rpl_topic,
            "353":self.handle_rpl_namreply
        }

        # A list of all the messages the client has receievd and printed for the user
        self.printed_messages = []

        # This can be set to True to terminate the object
        self.request_terminate = False
        

    # DO NOT EDIT THIS METHOD
    # Setup the client and start listening for incoming messages
    def run(self):
        self.print_info("Launching client %s@%s..." % (self.nick, self.hostname))
        self.connect_to_server()
        

    ######################################################################
    # This function is called to establish a connection with an IRC server and to send the USER
    # registration message. Once receiving the RPL_WELCOME response, the client should begin listening
    # for responses from the server.
    # NOTE: If we implement listening to functionality from the client, it should also be begun here
    # TODO: Connect to the server, send a USER registration message to the server, listen for a RPL_WELCOME response
    #       and begin listening for more messages from the server
    def connect_to_server(self):

        # setup TCP socket and connect to server
        self.clientSocket = socket(AF_INET, SOCK_STREAM) 
        self.clientSocket.connect((self.serveraddr, int(self.serverport)))

        # USER registration message
        msg = "USER " + self.nick + " " + self.hostname + " " + self.servername + " :" + self.realname + "\r\n"

        # send msg to server
        self.clientSocket.send(msg.encode())

        # get response from server
        response = self.clientSocket.recv(2048).decode()
        response = response.split(" ")

        """
        while response[1] != "1":
            response = self.clientSocket.recv(2048).decode()
            response = response.split(" ")
        """
        self.start_listening_to_server()
            

    # You should call this function when you are ready to start listening for messages from the server
    # You do not need to edit this function
    def start_listening_to_server(self):
        x = threading.Thread(target=self.listen_for_server_input)
        x.start()

    # This function listens for messages from the server.
    # TODO: Read respones from the server and put them into the server_read_buffer.
    #       Then begin processing the new message(s)
    def listen_for_server_input(self):
        while not self.request_terminate:
            msg = self.clientSocket.recv(2048).decode()
            self.server_read_buffer = self.server_read_buffer + msg
            self.process_server_input()


    # This function should start the process of handling messages received by the server. You will need to
    # perform several tasks:
    # 1. Split the data into distinct messages, in case the data in the recv buffer contains several commands
    # 2. Separate each message into three variables: prefix, command, and params
    #    prefix should be None if no prefix is present
    #    command should be a string containing the command word, or response number
    #    params should be a list containing the parameters included in the message. If no params
    #    we included, then params should be None
    # 3. After separating the prefix, command, and params, you should then call
    #    self.message_handlers[command](select_key, prefix, command, params) for each message
    #    This will call the correct function (defined below) for the message you have received
    # 4. Clear the read buffer so you don't process a message twice
    # TODO: Write this function, including all of the functionality described above. You are encouraged
    #       to create several methods that are called by process_data to handle each of these required effects
    def process_server_input(self):
        if self.server_read_buffer:
            prefix = None
            command = None
            params = None

            # check for multiple messages with split on \r\n
            msg = recv_data.split("\r\n")

            for item in msg:
                if item != '':
                    trailing = []
                    if item[0] == ':':
                        prefix, item = item[1:].split(' ', 1)
                    if item.find(' :') != -1:
                        item, trailing = item.split(' :', 1)
                        params = item.split()
                        params.append(trailing)
                    else:
                        params = item.split()
                    command = params.pop(0)
                    self.message_handlers[command](select_key, prefix, command, params)
            self.server_read_buffer = ""




    ######################################################################
    # This function should send a message to the server
    def send_message_to_server(self, message):
        self.clientSocket.send(message.encode())




    # Stores the printed messages in a list, so the testing framework can evaluate the messages received
    # You may add to this function, but make sure that you still append messages to the printed_messages list
    def print_message_to_user(self, message):
        self.printed_messages.append(message)




    ######################################################################
    # This block of functions ...
    # def listen_for_user_input(self):
    #     while not self.request_terminate:
    #         user_input = input(">>>")
    #         self.process_user_input(user_input)

    # def process_user_input(self, user_input):
    #     pass

    ######################################################################
    # The remaining functions are command handlers. Each command handler is documented
    # with the functionality that must be supported
    
    ######################################################################
    # Quit message
    # Command: QUIT
    # Parameters: 
    #   {[<Quit message>]}: an optional message from the user who has quit. If no message is provided,  
    #                     use the default message: <nick> has quit  
    # Examples: 
    #   QUIT                                        # A message without a quit message
    #   QUIT :shot with an arrow in the chest       # A message with a quit message
    # Expected numeric replies: 
    #   None
    def quit(self, quit_message=None):

        #Quit WITHOUT an optional message
        if quit_message == None:
            msg = "QUIT\r\n"
            self.clientSocket.send(msg.encode())
        #Quit WITH an optional message
        else:
            msg = "QUIT :" + quit_message + "\r\n"
            self.clientSocket.send(msg.encode())

    


    ######################################################################
    # Join message
    # Command: JOIN
    # Parameters: 
    #   <channel> 
    #   [<key>]
    # Examples: 
    #   JOIN #Orcs4Isengard             # Join the channel #Orcs4Isengard without a password, 
    #                                   # or create the channel if it does not exist 
    #   JOIN #Orcs4Isengard fubar       # Join the channel #Orcs4Isengard with the password fubar, 
    #                                   # or create the channel with that password if it does not exist
    # Expected numeric replies: 
    #   ERR_NEEDMOREPARAMS
    #   ERR_BADCHANNELKEY
    #   RPL_TOPIC
    def join(self, channel, key=None):
        pass
        



    ######################################################################
    # Part message
    # Command: PART
    # Parameters: 
    #   <channel>
    # Examples: 
    #   PART #Orcs4Isengard             # Leave the channel #Orcs4Isengard
    # Numeric replies:  
    #   ERR_NEEDMOREPARAMS 
    #   ERR_NOSUCHCHANNEL
    #   ERR_NOTONCHANNEL 
    def part(self, channel):
        pass




    ######################################################################
    # Topic message
    # Command: TOPIC
    # Parameters: 
    #   <channel> 
    #   [<topic>]
    # Examples: 
    #   TOPIC #RingBearers                              # Request the topic for the channel #RingBearers
    #   TOPIC #RingBearers :Best uses for invisibility  # Sets the topic for the channel #RingBearers to 
    #                                                   # Best uses for invisibility
    # Numeric replies:  
    #   ERR_NEEDMOREPARAMS, 
    #   ERR_NOTONCHANNEL 
    #   RPL_NOTOPIC 
    #   RPL_TOPIC
    def topic(self, channel, topic=None):
        pass




    ######################################################################
    # Names message
    # Command: NAMES
    # Parameters: 
    #   [<channel>]
    # Examples: 
    #   NAMES
    #   NAMES #RingBearers
    # Numeric replies:  
    #   RPL_NAMREPLY
    def names(self, channel=None):
        pass




    ######################################################################
    # Private message 
    # Command: PRIVMSG
    # Parameters: 
    #   <receiver>
    #   <text to be sent>
    # Examples: :
    #   Angel PRIVMSG Wiz :Hello are you receiving this message ?
    #   PRIVMSG Angel :yes I'm receiving it !receiving it !'u>(768u+1n) .br
    #   PRIVMSG jto@tolsun.oulu.fi :Hello !
    #   PRIVMSG $*.fi :Server tolsun.oulu.fi rebooting
    #   PRIVMSG #*.edu :NSFNet is undergoing work, expect interruptions
    # Numeric replies:  
    #   ERR_NORECIPIENT, 
    #   ERR_NOTEXTTOSEND, 
    #   ERR_CANNOTSENDTOCHAN,
    #   ERR_NOTOPLEVEL, 
    #   ERR_WILDTOPLEVEL,
    #   ERR_TOOMANYTARGETS, 
    #   ERR_NOSUCHNICK, 
    #   RPL_AWAY 
    def privmsg(self, receiver, message):
        pass


    

    ######################################################################
    # The remaining functions are command handlers. Each command handler is documented
    # with the functionality that must be supported.
    #
    # Each function should call self.print_message_to_user(" ".join(params)) to log
    # the response message that was received for analysis by the testing framework.
    ######################################################################
    def handle_rpl_notopic(self, prefix, params):
        self.print_message_to_user(" ".join(params))
        # TODO: Finish updating the client state based on this message



    def handle_rpl_topic(self, prefix, params):        
        self.print_message_to_user(" ".join(params))
        # TODO: Finish updating the client state based on this message




    def handle_rpl_namreply(self, prefix, params):
        # When working with the reply, store the list of names in the nicks variable.
        # This is required for the print_message_to_user to function as the tester expects
        nicks = []
        self.print_message_to_user("%s %s" % (params[0], " ".join(nicks)))
        
        # TODO: Finish updating the client state based on this message




    ######################################################################
    # This block of functions enables logging of info, debug, and error messages
    # Do not edit these functions. init_logging() is already called by the template code
    # You are encouraged to use print_info, print_debug, and print_error to log
    # messages useful to you in development

    def init_logging(self):
        # If we don't include a log file name, then don't log
        if not self.log_file:
            return

        # Get a reference to the logger for this program
        self.logger = logging.getLogger("IRCServer")

        # Create a file handler to store the log files
        fh = logging.FileHandler(self.log_file, mode='w')

        # Set up the logging level. It defaults to INFO
        log_level = logging.INFO
        if self.debug:
            log_level = logging.DEBUG
        
        # Define a formatter that will be used to format each line in the log
        formatter = logging.Formatter(
            ("%(asctime)s - %(name)s[%(process)d] - "
             "%(levelname)s - %(message)s"))

        # Assign all of the necessary parameters
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        self.logger.setLevel(log_level)
        self.logger.addHandler(fh)

    def print_info(self, msg):
        if self.verbose:
            print("%s:%s" % (self.servername,msg))
            sys.stdout.flush()
        if self.logger:
            self.logger.info(msg)

    def print_debug(self, msg):
        if self.debug:
            print("%s:%s" % (self.servername,msg))
            sys.stdout.flush()
        if self.logger:
            self.logger.debug(msg)

    def print_error(self, msg):
        sys.stderr.write("%s:%s\n" % (self.servername, msg))
        if self.logger:
            self.logger.error(msg)