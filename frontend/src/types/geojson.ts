/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Feature, FeatureCollection, LineString, Point } from "geojson";

/* -------------------------
   GeoJSON 用の型
------------------------- */

/** [lng, lat]（GeoJSON 座標順） */
export type LngLatTuple = [number, number];
/** [lat, lng]（UI / バックエンド座標順） */
export type LatLngTuple = [number, number];

/** 画像四隅ハンドルの ID */
export type ImageCornerId = "TL" | "TR" | "BL" | "BR";

/** 画像編集ハンドル（四隅 + 回転）のプロパティ */
export type ImageHandleProperties =
  | { id: ImageCornerId; kind: "corner" }
  | { id: "ROT"; kind: "rotate" };

export type ImageHandleFeatureCollection = FeatureCollection<Point, ImageHandleProperties>;
export type ImageFrameFeature = Feature<LineString, { id: string }>;
