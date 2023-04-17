import math


def airdrop_loc_lat_long(pos, vel, altitude):
    vel = (vel[0] * 360 / 40008000,
           vel[1] * 360 / (40075160 * math.cos(vel[1])))
    return (pos[0] - vel[0] * (altitude / 9.8) ** 0.5,
            pos[1] - vel[1] * (altitude / 9.8) ** 0.5)


if __name__ == '__main__':
    print(airdrop_loc_lat_long((30, 60), (100, 100), 100))
