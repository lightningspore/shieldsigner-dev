#!/bin/sh
# Pinned Luckfox kernel drivers only; deliberately excludes Rockit/MCU/rkipc.
set -eu
module_dir=/oem/usr/ko
for name in rk_dvbm videobuf2-memops videobuf2-common videobuf2-v4l2 \
  videobuf2-vmalloc videobuf2-cma-sg sc3336 video_rkcif video_rkisp \
  phy-rockchip-csi2-dphy-hw phy-rockchip-csi2-dphy; do
  sys_name=$(echo "$name" | tr '-' '_')
  if [ ! -d "/sys/module/$sys_name" ] && [ -f "$module_dir/$name.ko" ]; then
    insmod "$module_dir/$name.ko"
  fi
done
for name in video_rkcif video_rkisp; do
  echo 1 > "/sys/module/$name/parameters/clr_unready_dev"
done
udevadm settle --timeout=10
for node in /dev/video0 /dev/video11 /dev/video18 /dev/video19 /dev/video20; do
  test -c "$node"
done
! test -d /sys/module/rockit
