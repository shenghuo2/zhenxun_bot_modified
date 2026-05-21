pid=$(netstat -tunlp | grep 14755 | awk '{print $7}')
pid=${pid%/*}
kill -9 $pid
sleep 3
python3 bot.py