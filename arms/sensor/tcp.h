#ifndef TCP_H
#define TCP_H
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <winsock2.h>
#pragma comment(lib, "Ws2_32.lib")
typedef SOCKET SOCKET_HANDLE;
#else
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netdb.h>
#include <unistd.h>
typedef int SOCKET_HANDLE;
#endif

#include <sys/types.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#endif

typedef unsigned int uint32;
typedef int int32;
typedef unsigned short uint16;
typedef short int16;
typedef unsigned char byte;

typedef struct FTResponseStruct {
	uint16 header;
	uint16 status;
	int16 ForceX;
	int16 ForceY;
	int16 ForceZ;
	int16 TorqueX;
	int16 TorqueY;
	int16 TorqueZ;
} FTResponse;

typedef struct DResponseStruct {
	
	double Fx;
	double Fy;
	double Fz;
	double Tx;
	double Ty;
	double Tz;
} DResponse;

typedef struct CalibrationResponseStruct
{
	uint16 header;
	byte forceUnits;
	byte torqueUnits;
	uint32 countsPerForce;
	uint32 countsPerTorque;
	uint16 scaleFactors[6];
} CalibrationResponse;


typedef struct FTReadCommandStruct
{
	byte command;
	byte reserved[19];
}FTReadCommand;


typedef struct ReadCalibrationCommandStruct {
	byte command;
	byte reserved[19];
} ReadCalibrationCommand;



CalibrationResponse calibrationResponse;  // global variable to hold calibration info datas


extern void MySleep(unsigned long ms);
extern int Connect(SOCKET_HANDLE * handle, const char * ipAddress, uint16 port);
extern void Close(SOCKET_HANDLE * handle);
extern void ShowCalibrationInfo(CalibrationResponse * r);
extern int GetCalibrationInfo(SOCKET_HANDLE *socket);
extern int16 swap_int16(int16 val);
extern void SwapFTResponseBytes(FTResponse * r);
extern int ReadFT(SOCKET_HANDLE * socket, FTResponse * r);
extern double* ShowResponse(FTResponse * r);
extern void sensorConnect(char * ipaddr);
extern void sensorDisconnect(void);
extern DResponse sensorRead(void);
