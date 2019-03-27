#define STARTANALOG 0
#define ENDANALOG 100
#define IDPOS 0
#define STARTBYTE 2
#define STARTBYTEPOSITION 0
#define COMMANDBYTEPOSITION 1
#define LENBYTEPOSITION 2
#define DATABYTEPOSITION 3
#define CMD_IDENTIFY 255
#define CMD_IDENTIFY_LENGTH 0
#define CMD_GETFIMWARE 254
#define CMD_GETFIMWARE_LENGTH 0
#define MAXFUNCTIONS 6
#define SERIALARRAYSIZE 13
#define BAUD 9600
#define DATARATE 200
#define FIRMWARE 0
#include <EEPROM.h>
#include <HX711.h>
uint8_t dout = 2;
uint8_t sck = 3;
uint8_t writedata[SERIALARRAYSIZE];
uint8_t serialread[SERIALARRAYSIZE];
uint8_t serialreadpos = 0;
uint8_t commandlength = 0;
uint8_t cmds[MAXFUNCTIONS ];
uint8_t cmd_length[MAXFUNCTIONS];
void (*cmd_calls[MAXFUNCTIONS])(uint8_t* data, uint8_t s);
uint32_t lastdata = 0;
uint32_t ct;
uint32_t datarate = DATARATE;
uint8_t c;
bool identified = false;
HX711 hx711;
uint8_t average = 1;
uint8_t gain = 64;
uint16_t generate_checksum(uint8_t* data, int count){
uint16_t sum1 = 0;
uint16_t sum2 = 0;
for (int index = 0; index < count; ++index ) {
sum1 = (sum1 + data[index]) % 255;
sum2 = (sum2 + sum1) % 255;
}
return (sum2 << 8) | sum1;
}
void write_data_array(uint8_t* data, uint8_t cmd, uint8_t len){
writedata[STARTBYTEPOSITION] = STARTBYTE;
writedata[COMMANDBYTEPOSITION] = cmd;
writedata[LENBYTEPOSITION] = len;
for (uint8_t i = 0; i < len; i++) {
writedata[DATABYTEPOSITION + i] = data[i];
}uint16_t cs = generate_checksum(writedata, len + DATABYTEPOSITION);
writedata[DATABYTEPOSITION + len] = cs >> 8;
writedata[DATABYTEPOSITION + len + 1] = cs >> 0;
Serial.write(writedata, len + DATABYTEPOSITION + 2);
}
template< typename T> void write_data(T data, uint8_t cmd){
uint8_t d[sizeof(T)];
for (uint8_t i = 0;i<sizeof(T) ; i++) {
d[i] = (uint8_t) (data >> (8 * i) & 0xff );
}
write_data_array(d, cmd, sizeof(T));
}
uint64_t get_id(){
uint64_t id;
EEPROM.get(IDPOS, id);
return id;
}
void checkUUID(){
uint64_t id = get_id();
uint16_t cs = generate_checksum((uint8_t*)&id, sizeof(id));
uint16_t cs2;
EEPROM.get(IDPOS + sizeof(id), cs2);
if (cs != cs2) {
id = (uint64_t)((((uint64_t)random()) << 48) | (((uint64_t)random()) << 32) | (((uint64_t)random()) << 16) | (((uint64_t)random())));
EEPROM.put(IDPOS, id);
EEPROM.put(IDPOS + sizeof(id), generate_checksum((uint8_t*)&id, sizeof(id)));
}
}
void add_command(uint8_t cmd, uint8_t len, void (*func)(uint8_t* data, uint8_t s)){
for (uint8_t i = 0; i < MAXFUNCTIONS; i++ ) {
if (cmds[i] == 255) {
cmds[i] = cmd;
cmd_length[i] = len;
cmd_calls[i] = func;
return;
}
}
}
void endread(){
commandlength = 0;
serialreadpos = STARTBYTEPOSITION;
}
uint8_t get_cmd_index(uint8_t cmd){
for (uint8_t i = 0; i < MAXFUNCTIONS; i++ ) {
if (cmds[i] == cmd) {
return i;
}
}
return 255;}
void validate_serial_command(){
if(generate_checksum(serialread, DATABYTEPOSITION + serialread[LENBYTEPOSITION]) == (uint16_t)(serialread[DATABYTEPOSITION + serialread[LENBYTEPOSITION]] << 8) + serialread[DATABYTEPOSITION + serialread[LENBYTEPOSITION]+1]){
uint8_t cmd_index = get_cmd_index(serialread[COMMANDBYTEPOSITION]);
if(cmd_index != 255){
uint8_t data[serialread[LENBYTEPOSITION]];
memcpy(data,&serialread[DATABYTEPOSITION],serialread[LENBYTEPOSITION]);
cmd_calls[cmd_index](data,serialread[LENBYTEPOSITION]);
}
}
}
uint64_t readloop(){
while(Serial.available() > 0) {
c = Serial.read();
serialread[serialreadpos] = c;
if (serialreadpos == STARTBYTEPOSITION) {
if (c == STARTBYTE) {
} else {
endread();
continue;
}
}
else {
if (serialreadpos == LENBYTEPOSITION) {
commandlength = c;
} else if (serialreadpos - commandlength > DATABYTEPOSITION + 1 ) { //stx cmd len cs cs (len = 0; pos = 4)
endread();
continue;
}
else if (serialreadpos - commandlength == DATABYTEPOSITION + 1) {
validate_serial_command();
endread();
continue;
}
}
serialreadpos++;
}
}
void identify_0(uint8_t* data, uint8_t s){
identified=data[0];if(!identified){uint64_t id = get_id();write_data(id,0);}}
void get_fw_1(uint8_t* data, uint8_t s){
write_data((uint64_t)FIRMWARE,1);}
void datarate_2(uint8_t* data, uint8_t s){
uint32_t temp;memcpy(&temp,data,4);if(temp>0){datarate=temp;}write_data(datarate,2);}
void dout_3(uint8_t* data, uint8_t s){
if(data[0]>0){dout=data[0];}write_data(dout,3);pinMode(dout, OUTPUT);}
void sck_4(uint8_t* data, uint8_t s){
if(data[0]>0){sck=data[0];}write_data(sck,4);pinMode(sck, OUTPUT);}
void read_data_5(uint8_t* data, uint8_t s){
write_data(hx711.read_average(average),5);}
void start_hx711(){
hx711.begin(dout, sck,gain);
}

void dataloop(){
write_data(hx711.read_average(average),5);
}

void loop(){
readloop();
ct = millis();
if(ct-lastdata>datarate && identified){
dataloop();
lastdata=ct;
}
Serial.println(hx711.read_average(average),5);
}

void setup(){
Serial.begin(BAUD);
while (!Serial) {;}
for (int i = STARTANALOG; i < ENDANALOG; i++) {
randomSeed(analogRead(i)*random());
}
checkUUID();
for (uint8_t i = 0; i < MAXFUNCTIONS; i++ ) {
cmds[i] = 255;
}
ct = millis();
pinMode(dout, OUTPUT);
pinMode(sck, OUTPUT);
add_command(0, 1, identify_0);
add_command(1, 0, get_fw_1);
add_command(2, 4, datarate_2);
add_command(3, 1, dout_3);
add_command(4, 1, sck_4);
add_command(5, 1, read_data_5);
start_hx711();

}
