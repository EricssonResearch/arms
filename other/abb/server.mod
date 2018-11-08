MODULE server
    !***********************************************************
    !
    ! Module:  server
    !
    ! Description:
    !   This module allows remote computers to access the RAPID API via socket communication.
    !
    !       -	The ABB robot acts as a server, hence the remote computer has to be configured
	!		  	as a client.
    !
    !       -	When a socket error occurs, the server will be restarted automatically.
    !
    !       -	Messages of the following form are expected:
    !
    !           <length of the original message in bytes><delimiter><original message>
    !           or in short form: <l><d><m>
    !
    !           The <length of the original message in bytes> = <l> has to be provided as an integer
    !           number, whereby the delimiter and the original message have to be of the following
	!           form:
    !
    !               <delimiter> = <d> = \n = \0A
    !               <original message> = <m> = array of size 10; max. 80 bytes
    !                   ->	The first element represents the id number and therefore a specific case.
	!						Each case can consist of several RAPID commands which will be
	!						executed once the received message is fully interpretated.
    !                      	For more details see the example below or the code (TEST -
	!						CASE instruction).
    !                   ->	The remaining nine elements can be used for data, e.g. coordinates.
    !
    !           Example in Python 3.6:
    !
    !               socket.send(b"21\n[0,1,2,3,4,5,6,7,8,9]")
    !
    !           , where
    !               <length of the original message in bytes> = <l> = 21
    !               <delimiter> = <d> = \n = \0A
    !               <original message> = <m> = [0,1,2,3,4,5,6,7,8,9]
    !                   ->	id = 0, which will close the current connection; see below (TEST -
	!					CASE instruction).
    !                   ->	The remaining entries (1-9) can be arbitrary in this case, since they
	!					    are not needed to close the connection. But because an array of size 10
	!					    is expected, they have to be filled out.
    !
    !       -   The sequence <l><d><m>, see above, is called command request.
    !
    !       -   A message can contain several command requests. Thereby no separation/delimiter is
    !           needed. E.g. '<l><d><m><l><d><m>'.
    !
    !       - 	After a message is sent to and fulfilled by the ABB robot, the ABB robot sends an
	!			answer to the client if respond = TRUE.
    !           -> 	The message is in JSON format with the entries:
    !
    !                   {'id':<id number>,'ok':<bool>,'data': <array of variable size>}
    !
    !               , where
    !
    !                   <id number>:    If the received message does not contain any errors, this id
	!									number equals the id number in the received message.
	!									Otherwise it represents an error code (negative number).
    !                   <ok>:	If equals 0, an error occurred during the operation, otherwise not.
    !                   <array of variable size>:	Represents the data to send back to the client.
	!												Can be of variable size; the content depends on
	!												the executed case and therefore the id number in
    !                                               the received message.
    !
    ! For more details visit: https://github.com/EricssonResearch/arms
    !
    ! Author: HK team 2018
    !
    ! Version: 0.7
    !
    !***********************************************************


    !******************
    !Global variables.
    !******************
    PERS string host := "127.0.0.1";
    PERS num port := 5001;
    VAR socketdev server_socket;
    VAR socketdev client_socket;
    PERS num one_byte := 1;
    VAR bool ok;


    !************
    !Procedures.
    !************
    PROC ServerCreateAndConnect(string host, num port)
        !Creates a server and listens for incoming connections.
        !The first client which tries to connect will be accepted.
        !
        ! Args:
        !   host: Represents either a hostname in internet domain notation or an IPv4 address.
        !   port: Port number (integer).
        !
        ! Attributes:
        !   client_ip: The address bound to the socket on the other end of the connection.

        VAR string client_ip;

        SocketCreate server_socket;
        SocketBind server_socket, host, port;
        TPWrite "SERVER: Created server at (host, port)=(" + host + ", " + ValToStr(port) + ").";
        SocketListen server_socket;
        TPWrite "SERVER: Listening for incoming connections.";
        WHILE SocketGetStatus(client_socket) <> SOCKET_CONNECTED DO
            SocketAccept server_socket, client_socket \ClientAddress:=client_ip \Time:=WAIT_MAX;
            IF SocketGetStatus(client_socket) <> SOCKET_CONNECTED THEN
                TPWrite "SERVER: Problem serving an incoming connection.";
                TPWrite "SERVER: Try reconnecting.";
            ENDIF
            !Wait some time for the next reconnection.
            WaitTime 0.5;
        ENDWHILE
        TPWrite "SERVER: Connected to client with IP: " + client_ip + ".";
    ENDPROC

    PROC main()
        !This prodecure does the following:
        !   1. Gives the command to create a server.
        !   2. Handles the communication with the client.
        !       -   If the received message is faulty or can not be addressed, an error code will
        !           be send back to the client.
        !       -   If the received message is of the expected form, the addressed case will be
        !           executed.
        !       -   If respond = TRUE, an answer/respond will be send to the client.
        !   3. Includes error handling. In most cases the server will be restarted and the last
        !      (faulty) command will be retried to execute once the connection is rebuilt.
        !
        ! Attributes:
        !   --- Receiving a message from the remote computer. ---
        !   recv_string: Stores the received string data.
        !   length_string: Stores the length of the original message to receive as a string.
        !   length: Stores the into a numeric value casted/converted variable 'length_string'.
        !   recv_params{10}: Represents the original message to receive as an array.
        !   id: The value with which the test value will be compared (TEST - CASE instruction).
        !
        !   --- Sending a message to the remote computer. ---
        !   respond: If TRUE, a answer/respond message will be send, otherwise not.
        !   send_length: The length of 'send_string' which has to be send beforehand.
        !   send_string: The original message to send.
        !   ok_string: Represents the boolean variable 'ok' as a string; 0 = FALSE, 1 = TRUE.
        !   data_string: The data to send, separated by a comma.
        !
        !   --- Other. ---
        !   joints_pose: Represents the current joint pose/coordinates.

        VAR string recv_string;
        VAR string length_string;
        VAR num length;
        VAR num recv_params{10};
        VAR num id;

        VAR bool respond;
        VAR string send_length;
        VAR string send_string;
        VAR string ok_string;
        VAR string data_string;

        VAR jointtarget joints_pose;

        !Create server.
        ServerCreateAndConnect host, port;

        !Main procedure.
        WHILE TRUE DO
            !Reset flow variables.
            ok := TRUE;
            recv_string := "";
            length_string := "";
            length := 0;
            respond := TRUE;
            data_string := "";

            !----------------------------------------------------
            !Receive data from the socket (client) in two steps.
            !----------------------------------------------------

            !1. step:   Get the length of the message.
            WHILE recv_string <> "\0A" DO
                length_string := length_string + recv_string;
                SocketReceive client_socket \Str:=recv_string \ReadNoOfBytes:=one_byte \Time:=WAIT_MAX;
                IF StrFind(recv_string,1,STR_DIGIT) <> 1 AND StrFind(recv_string,1,"\0A") <> 1 THEN
                    recv_string := "";
                    length_string := "";
                ENDIF
            ENDWHILE

            !2. step:   Receive the original message with respect to step one.
            !           The following error codes are introduced, ok = FALSE:
            !               1) id = -2: The received length l of the original message exceeds the
            !                           bounds 0 < l <= 80.
            !                           OR: The length could not be read/ casted into a number.
            !               2) id = -3: The received original message could not be casted into an
            !                           array.
            !               3) id = -4: The received length is greater than the actual length of the
            !                           original message.
            !               4) id = -5: The received id number is below zero, which is not allowed
            !                           since the id numbers < 0 are reserved for error codes.
            !           Note that the first matching error code will be assigned to id.
            ok:= StrToVal(length_string, length);
            IF ok = TRUE AND length > 0 AND length <= 80 THEN
                SocketReceive client_socket \Str:=recv_string \ReadNoOfBytes:=length \Time:=WAIT_MAX;
                ok := StrToVal(recv_string, recv_params);
                IF ok = TRUE THEN
                    IF StrLen(recv_string) = length THEN
                        id := recv_params{1};
                        IF id < 0 THEN
                            id := -5;
                        ENDIF
                    ELSE
                        ok := FALSE;
                        id := -4;
                    ENDIF
                ELSE
                    id := -3;
                ENDIF
            ELSE
                ok := FALSE;
                id := -2;
            ENDIF

            !-----------------------------------------------------------------------------
            !Find the case belonging to the id number and execute the respective commands.
            !-----------------------------------------------------------------------------
            TEST id
                CASE 0: !Close connection.
                    TPWrite "SERVER: The client has closed the connection.";

                    !Close server.
                    SocketClose client_socket;
                    SocketClose server_socket;

                    !Reinitiate server.
                    ServerCreateAndConnect host, port;

                    !Do not send a respond.
                    respond := FALSE;

                CASE 1: !Get system informations.
                    TPWrite "SERVER: Send sytem information to client.";
                    data_string := GetSysInfo(\SerialNo) + ", ";
                    data_string := data_string + GetSysInfo(\SWVersion) + ", ";
                    data_string := data_string + GetSysInfo(\RobotType);

                CASE 10: !Get joint coordinates.
                    TPWrite "SERVER: Send joint coordinates to client.";
                    joints_pose := CJointT();
                    data_string := NumToStr(joints_pose.robax.rax_1,2) + ", ";
                    data_string := data_string + NumToStr(joints_pose.robax.rax_2,2) + ", ";
                    data_string := data_string + NumToStr(joints_pose.robax.rax_3,2) + ", ";
                    data_string := data_string + NumToStr(joints_pose.robax.rax_4,2) + ", ";
                    data_string := data_string + NumToStr(joints_pose.robax.rax_5,2) + ", ";
                    data_string := data_string + NumToStr(joints_pose.robax.rax_6,2);

                DEFAULT:
                    TPWrite "SERVER: Illegal (not addressed) id number: " + ValToStr(id) + ".";
                    !The error codes have to be kept, otherwise set id = -1 to indicate that there
                    !is currently not a case belonging to the received id number.
                    IF id >= 0 THEN
                        id := -1;
                    ENDIF
                    !Error occurred.
                    ok := FALSE;
            ENDTEST

            !---------------------------------------------------
            !Send an answer in JSON format back to the client.
            !---------------------------------------------------
            IF respond = TRUE AND SocketGetStatus(client_socket) = SOCKET_CONNECTED THEN
                !Convert the bool variable 'ok' to a string; 1 = TRUE, 0 = FALSE.
                ok_string := "0";
                IF ok = TRUE THEN
                    ok_string := "1";
                ENDIF

                !Translate the message to send into JSON format.
                send_string := "{'id':" + NumToStr(id, 0) + ",";
                send_string := send_string + "'ok':" + ok_string + ",";
                send_string := send_string + "'data': '[" + data_string + "]'}";

                !+++++++++++++++++++++++++++++++++++++++++++++++
                !Send data to the socket (client) in two steps.
                !+++++++++++++++++++++++++++++++++++++++++++++++

                !1. step:   Send the length of the message.
                send_length := NumToStr(StrLen(send_string), 0) + "\0A";
                SocketSend client_socket \Str:=send_length;

                !2. step:   Send the original message.
                SocketSend client_socket \Str:=send_string;
		    ENDIF
        ENDWHILE

    ERROR (LONG_JMP_ALL_ERR)
        TPWrite "SERVER: Error Handler - " + NumtoStr(ERRNO,0) + ".";
        TEST ERRNO
            CASE ERR_SOCK_CLOSED:
                TPWrite "SERVER: Lost connection to the client.";
                TPWrite "SERVER: The socket will be closed and restarted.";
                !Close server.
                SocketClose client_socket;
                SocketClose server_socket;
                !Reinitiate server.
                ServerCreateAndConnect host, port;
                !Retry last command.
                RETRY;
            CASE ERR_OUTOFBND:
                !The array index is outside the permitted limits.
                ok := FALSE;
            DEFAULT:
                TPWrite "SERVER: Unknown error.";
                TPWrite "SERVER: The socket will be closed and restarted.";
                !Close server.
                SocketClose client_socket;
                SocketClose server_socket;
                !Reinitiate server.
                ServerCreateAndConnect host, port;
                !Retry last command.
                RETRY;
        ENDTEST
    ENDPROC
ENDMODULE