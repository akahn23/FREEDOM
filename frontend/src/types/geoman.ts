/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Map as MaplibreMap } from "maplibre-gl";
import type {
  BasicGeometry,
  FeatureId,
  Geoman,
  GmFwdEventNameWithPrefix,
  ImportGeoJsonProperties,
} from "@geoman-io/maplibre-geoman-free";

/* -------------------------
   Geoman (@geoman-io/maplibre-geoman-free 0.8.x) 用の型
------------------------- */

export type {
  BasicGeometry,
  FeatureData,
  FeatureId,
  FeatureSourceName,
  GeoJsonImportFeature,
  GeoJsonImportFeatureCollection,
  GeoJsonShapeFeature,
  GeoJsonShapeFeatureCollection,
  GmFwdEventNameWithPrefix,
  ImportGeoJsonProperties,
} from "@geoman-io/maplibre-geoman-free";

/** Geoman インスタンスをキャッシュする MapLibre Map（`map.gm`） */
export type MaplibreMapWithGeoman = MaplibreMap & { gm?: Geoman };

/** importGeoJson による部分上書き内容 */
export interface GeomanFeaturePatch {
  geometry?: BasicGeometry | null;
  properties?: ImportGeoJsonProperties;
}

/** ID 抽出対象（Geoman export / MapLibre feature の共通部分） */
export interface GmFeatureIdSource {
  id?: FeatureId | null;
  properties?: Record<string, unknown> | null;
}

/** 地図に登録する Geoman 転送イベントとハンドラの組 */
export type GmEventBinding = readonly [GmFwdEventNameWithPrefix, () => void];
