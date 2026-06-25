import argparse
import time

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.obstacles_avoid.obstacles_avoid_client import ObstaclesAvoidClient
from unitree_sdk2py.go2.sport.sport_client import SportClient


IFACE = "ethrobot"

WALK_SPEED_MPS = 0.2
WALK_DURATION_S = 5.0
LATERAL_SPEED_MPS = 0.15
LATERAL_DURATION_S = 3.0
ROTATE_SPEED_RADPS = 0.4
ROTATE_DURATION_S = 2.0
MOVE_COMMAND_HZ = 20.0


def initialize_channel():
    ChannelFactoryInitialize(0, IFACE)


def make_sport_client():
    client = SportClient()
    client.SetTimeout(3.0)
    client.Init()
    return client


def make_obstacle_client():
    client = ObstaclesAvoidClient()
    client.SetTimeout(3.0)
    client.Init()
    return client


def stop_sport(sport_client):
    try:
        print("Sport StopMove:", sport_client.StopMove())
    except Exception as exc:
        print("Warning: SportClient StopMove failed:", exc)

    try:
        print("Sport zero Move:", sport_client.Move(0.0, 0.0, 0.0))
    except Exception as exc:
        print("Warning: SportClient zero Move failed:", exc)


def stop_obstacle(obstacle_client):
    try:
        print("Obstacle zero Move:", obstacle_client.Move(0.0, 0.0, 0.0))
    except Exception as exc:
        print("Warning: obstacle zero Move failed:", exc)


def enable_classic_walk(sport_client):
    print("ClassicWalk:", sport_client.ClassicWalk(True))
    time.sleep(0.5)


def enable_obstacle_api(obstacle_client):
    print("SwitchGet before:", obstacle_client.SwitchGet())

    while not obstacle_client.SwitchGet()[1]:
        print("SwitchSet:", obstacle_client.SwitchSet(True))
        time.sleep(0.1)

    print("SwitchGet after:", obstacle_client.SwitchGet())
    print("UseRemoteCommandFromApi true:", obstacle_client.UseRemoteCommandFromApi(True))


def release_obstacle_api(obstacle_client):
    stop_obstacle(obstacle_client)
    try:
        print("UseRemoteCommandFromApi false:", obstacle_client.UseRemoteCommandFromApi(False))
    except Exception as exc:
        print("Warning: disabling obstacle remote API failed:", exc)


def repeated_obstacle_move(obstacle_client, vx, vy, vyaw, duration_s):
    period_s = 1.0 / MOVE_COMMAND_HZ
    end_time = time.monotonic() + duration_s

    while time.monotonic() < end_time:
        obstacle_client.Move(vx, vy, vyaw)
        time.sleep(period_s)


def walk_forward(sport_client, obstacle_client):
    enable_classic_walk(sport_client)
    enable_obstacle_api(obstacle_client)

    print(
        "Walking forward with obstacle client: {:.2f} m/s for {:.1f}s.".format(
            WALK_SPEED_MPS,
            WALK_DURATION_S,
        )
    )

    try:
        repeated_obstacle_move(
            obstacle_client,
            vx=WALK_SPEED_MPS,
            vy=0.0,
            vyaw=0.0,
            duration_s=WALK_DURATION_S,
        )
    finally:
        release_obstacle_api(obstacle_client)
        stop_sport(sport_client)


def walk_backward(sport_client, obstacle_client):
    enable_classic_walk(sport_client)
    enable_obstacle_api(obstacle_client)

    print(
        "Walking backward with obstacle client: {:.2f} m/s for {:.1f}s.".format(
            -WALK_SPEED_MPS,
            WALK_DURATION_S,
        )
    )

    try:
        repeated_obstacle_move(
            obstacle_client,
            vx=-WALK_SPEED_MPS,
            vy=0.0,
            vyaw=0.0,
            duration_s=WALK_DURATION_S,
        )
    finally:
        release_obstacle_api(obstacle_client)
        stop_sport(sport_client)


def strafe(sport_client, obstacle_client, direction):
    if direction not in {"left", "right"}:
        raise ValueError("direction must be left or right")

    enable_classic_walk(sport_client)
    enable_obstacle_api(obstacle_client)

    vy = LATERAL_SPEED_MPS if direction == "left" else -LATERAL_SPEED_MPS

    print(
        "Walking {} with obstacle client: vy={:.2f} m/s for {:.1f}s.".format(
            direction,
            vy,
            LATERAL_DURATION_S,
        )
    )

    try:
        repeated_obstacle_move(
            obstacle_client,
            vx=0.0,
            vy=vy,
            vyaw=0.0,
            duration_s=LATERAL_DURATION_S,
        )
    finally:
        release_obstacle_api(obstacle_client)
        stop_sport(sport_client)


def rotate(sport_client, obstacle_client, direction):
    if direction not in {"left", "right"}:
        raise ValueError("direction must be left or right")

    enable_classic_walk(sport_client)
    enable_obstacle_api(obstacle_client)

    vyaw = ROTATE_SPEED_RADPS if direction == "left" else -ROTATE_SPEED_RADPS

    print(
        "Rotating {} with obstacle client: {:.2f} rad/s for {:.1f}s.".format(
            direction,
            vyaw,
            ROTATE_DURATION_S,
        )
    )

    try:
        repeated_obstacle_move(
            obstacle_client,
            vx=0.0,
            vy=0.0,
            vyaw=vyaw,
            duration_s=ROTATE_DURATION_S,
        )
    finally:
        release_obstacle_api(obstacle_client)
        stop_sport(sport_client)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=[
        "check",
        "stop",
        "stand",
        "sit",
        "stand_down",
        "recover",
        "walk_forward",
        "walk_backward",
        "walk_left",
        "walk_right",
        "rotate_left",
        "rotate_right",
        "release",
    ])
    args = parser.parse_args()

    print("Initializing Go2 channel on", IFACE)
    initialize_channel()
    print("Channel ready.")

    sport_client = make_sport_client()
    obstacle_client = make_obstacle_client()

    try:
        if args.command == "check":
            print("Obstacle SwitchGet:", obstacle_client.SwitchGet())

        elif args.command == "stop":
            print("Stopping.")
            stop_obstacle(obstacle_client)
            stop_sport(sport_client)

        elif args.command == "release":
            print("Releasing obstacle API.")
            release_obstacle_api(obstacle_client)
            stop_sport(sport_client)

        elif args.command == "stand":
            print("Standing.")
            print("StandUp:", sport_client.StandUp())

        elif args.command == "sit":
            print("Sitting.")
            print("Sit:", sport_client.Sit())

        elif args.command == "stand_down":
            print("Standing down.")
            print("StandDown:", sport_client.StandDown())

        elif args.command == "recover":
            print("Recovery stand.")
            print("RecoveryStand:", sport_client.RecoveryStand())

        elif args.command == "walk_forward":
            walk_forward(sport_client, obstacle_client)

        elif args.command == "walk_backward":
            walk_backward(sport_client, obstacle_client)

        elif args.command == "walk_left":
            strafe(sport_client, obstacle_client, "left")

        elif args.command == "walk_right":
            strafe(sport_client, obstacle_client, "right")

        elif args.command == "rotate_left":
            rotate(sport_client, obstacle_client, "left")

        elif args.command == "rotate_right":
            rotate(sport_client, obstacle_client, "right")

    finally:
        print("Done.")


if __name__ == "__main__":
    main()
