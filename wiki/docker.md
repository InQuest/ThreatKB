## Docker Installation  
1. Edit docker-compose.yml if you change to change defaults such as ports or credentials
2. Build the Docker image: `docker build -t threatkb .`
3. Execute docker-compuse: `docker-compose up`
4. Open your browser to htp://127.0.0.1:5000/#!/login

**Example output:**
```
$ docker-compose up
-Starting inquestkb_db_1 ... 	
-Starting inquestkb_db_1 ... done
-Recreating inquestkb_threatkb_1 ... 	
-Recreating inquestkb_threatkb_1 ... done
-Attaching to inquestkb_db_1, inquestkb_threatkb_1
-....snip...
-threatkb_1  |  * Debugger is active!
-threatkb_1  |  * Debugger PIN: 212-674-856
```
