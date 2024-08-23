## Service for cheking server availability
Can be launched on several servers, so they will monitor each other's availability, information about which can, for example, be sent through a Telegram bot:
![image](https://github.com/user-attachments/assets/bc32e529-9517-4b9a-8825-2e40c2c4c57a)

---

All you need is to specify the following parameters in [docker-compose.yml](https://github.com/Darveivoldavara/server_monitoring_system/blob/main/docker-compose.yml):
* Url to the server that requires monitoring
* Check and restart intervals
* Telegram bot token and group id with it
* SSL token for secure connections
* Full path to the server SSL certificate files where you run this service instance
