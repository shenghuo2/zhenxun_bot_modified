from mcstatus import JavaServer
import mcstatus.pinger,mcstatus.address



# mcstatus.JavaServer.async_status

ip = 'mc.hypixel.net'
ip = 'www.mctop1.top'
ip = 'mc.magicst.cn'
# server = JavaServer.lookup()
# server = mcstatus.address.minecraft_srv_address_lookup(ip

# )
server = JavaServer.lookup(ip)
print(server.status().description)

# print(server)