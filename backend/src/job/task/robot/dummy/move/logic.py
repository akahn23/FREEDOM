# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import math

from src import robot
from src.job import command
from src.job.task import abstract
from src.job.task.robot.dummy.move import Domain

# 地球半径（WGS84の平均値、メートル）
EARTH_RADIUS_M = 6_371_008.8


class Logic(abstract.statement.Logic[Domain]):
    """ダミー移動タスク処理"""
    async def init(self):
        """ジョブ開始時処理"""
        await super().init()
        self._robot = await self.domain.robot.make_logic(self._job_id, self._logger)
        self._location = await self.domain.location.make_logic(self._job_id, self._logger)
        self._speed = await self.domain.speed.make_logic(self._job_id, self._logger)
        if self.domain.stop:
            self._stop = await self.domain.stop.make_logic(self._job_id, self._logger)
        else:
            self._stop = None

    def haversine_distance_m(self, lat1, lon1, lat2, lon2):
        """ハバースインの公式で2点間距離（メートル）を計算"""
        φ1, λ1, φ2, λ2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dφ = φ2 - φ1
        dλ = λ2 - λ1
        a = math.sin(dφ/2)**2 + math.cos(φ1) * math.cos(φ2) * math.sin(dλ/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return 6_371_008.8 * c

    def initial_bearing_deg(self, lat1, lon1, lat2, lon2):
        """始方位角（真方位、度）を計算。大円航法の初期方位角。"""
        φ1, λ1, φ2, λ2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dλ = λ2 - λ1
        y = math.sin(dλ) * math.cos(φ2)
        x = math.cos(φ1) * math.sin(φ2) - math.sin(φ1) * math.cos(φ2) * math.cos(dλ)
        θ = math.atan2(y, x)
        bearing = (math.degrees(θ) + 360) % 360
        return bearing

    def destination_point(self, lat, lon, bearing_deg, distance_m):
        """
        始点(lat, lon)から方位(bearing_deg)へdistance_mだけ移動した点を返す（度）。
        球面三角法に基づく大円上の移動。
        """
        δ = distance_m / EARTH_RADIUS_M  # 角距離
        θ = math.radians(bearing_deg)
        φ1 = math.radians(lat)
        λ1 = math.radians(lon)

        φ2 = math.asin(math.sin(φ1)*math.cos(δ) + math.cos(φ1)*math.sin(δ)*math.cos(θ))
        λ2 = λ1 + math.atan2(math.sin(θ)*math.sin(δ)*math.cos(φ1),
                        math.cos(δ) - math.sin(φ1)*math.sin(φ2))

        lat2 = math.degrees(φ2)
        lon2 = (math.degrees(λ2) + 540) % 360 - 180  # 経度を[-180,180]に正規化
        return lat2, lon2

    async def exec(self):
        """タスク実行
        開始座標から目的地へ移動する
        生成AI製
        """
        dummy:robot.dummy.Node = await self._robot.exec()
        location:list[float] = await self._location.exec()
        target_lat, target_lon = location
        if not (-90 <= target_lat <= 90 and -180 <= target_lon <= 180):
            raise ValueError(f"Invalid coordinates: ({target_lat}, {target_lon})")
        speed_m_s = await self._speed.exec() * float(self.domain.meter) / float(self.domain.second)
        dt_s=dummy.domain.update_cycle
        tolerance_m=1.0

        try:
            while True:
                if self._stop and await self._stop.exec():
                    await asyncio.sleep(dt_s)
                    self.domain.command = [command.Text("停止中")]
                    continue

                lat, lon = dummy.domain.location
                remaining = self.haversine_distance_m(lat, lon, target_lat, target_lon)
                # 到着判定
                if remaining <= tolerance_m:
                    break

                # このステップで移動する距離
                step_dist = speed_m_s * dt_s
                # 残距離より長ければ、残距離分だけ移動して到達
                if step_dist >= remaining:
                    step_dist = remaining

                # 目的地への現在の方位角を計算
                bearing = self.initial_bearing_deg(lat, lon, target_lat, target_lon)

                # 次の位置を計算
                dummy.domain.location = list(self.destination_point(lat, lon, bearing, step_dist))

                self.domain.command = [command.Text("移動中")]
                await asyncio.sleep(dt_s)
        finally:
            self.domain.command.clear()
