/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

"use client";
import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useMap } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import "@geoman-io/maplibre-geoman-free/dist/maplibre-geoman.css";

import type {
  Feature,
  FeatureCollection,
  MultiPolygon,
  Polygon,
} from "geojson";
import type {
  Map as MaplibreMap,
  GeoJSONSource,
  LayerSpecification,
  MapLayerMouseEvent,
  MapMouseEvent,
} from "maplibre-gl";
import { Geoman, SOURCES, type GmOptionsPartial } from "@geoman-io/maplibre-geoman-free";
import type {
  FeatureData,
  FeatureSourceName,
  GeoJsonImportFeature,
  GeoJsonImportFeatureCollection,
  GeoJsonShapeFeature,
  GeoJsonShapeFeatureCollection,
  GeomanFeaturePatch,
  GmEventBinding,
  GmFeatureIdSource,
  ImportGeoJsonProperties,
  MaplibreMapWithGeoman,
} from "@/types/geoman";

import { Box } from "@mui/material";
import { useTranslations } from "next-intl";
import { MAP_Z_INDEX } from "@/components/map/mapZIndex";

import IntersectionAreaModeToggle from "./IntersectionAreaModeToggle";
import IntersectionListPanel from "./IntersectionListPanel";

// ---- Types ----
interface IntersectionDrawProps {
  onChange: (shapes: {
    entryShapes: IntersectionAreaGeoJSON[];
    reserveShapes: IntersectionAreaGeoJSON[];
  }) => void;
  initialShapes?: { entry_area: Area[]; reserve_area: Area[] };
}
type Area = {
  name: string;
  vertex_list: number[][];
  priority?: number;
};
type IntersectionAreaProps = {
  name: string;
  gm_id?: string;
  mode?: "entry" | "reserve";
  priority?: number;
  vertex_list?: number[][];
};
export type IntersectionAreaGeoJSON = Feature<Polygon, IntersectionAreaProps>;

// ---- Constants ----
const ENTRY_COLOR = "#3388ff";
const RESERVE_COLOR = "#ff9900";

const GM_SOURCE_ID_FALLBACK = "gm_main";
const EPS = 1e-12;

const LABEL_SRC_ID = "intersection-labels";
const LABEL_LAYER_ID = "intersection-labels-layer";

// ---- Utils ----
function sanitizeRing(coords: [number, number][]): [number, number][] {
  if (!Array.isArray(coords) || coords.length < 2) return coords;
  const [fx, fy] = coords[0] ?? [];
  const [lx, ly] = coords[coords.length - 1] ?? [];
  const same =
    Math.abs((fx ?? 0) - (lx ?? 1e9)) <= EPS &&
    Math.abs((fy ?? 0) - (ly ?? 1e9)) <= EPS;
  return same ? coords.slice(0, -1) : coords;
}
function ensureClosedRing(coords: [number, number][]): [number, number][] {
  if (!Array.isArray(coords) || coords.length === 0) return coords;
  const [fx, fy] = coords[0] ?? [];
  const [lx, ly] = coords[coords.length - 1] ?? [];
  const same =
    Math.abs((fx ?? 0) - (lx ?? 1e9)) <= EPS &&
    Math.abs((fy ?? 0) - (ly ?? 1e9)) <= EPS;
  return same ? coords : [...coords, [fx, fy]];
}
function extractOuterRing(
  geom: Polygon | MultiPolygon | null | undefined
): [number, number][] {
  if (!geom) return [];
  if (geom.type === "Polygon") {
    const ring = (geom.coordinates?.[0] ?? []) as [number, number][];
    return ring.filter(
      (p) => Array.isArray(p) && Number.isFinite(p[0]) && Number.isFinite(p[1])
    );
  }
  if (geom.type === "MultiPolygon") {
    const ring = (geom.coordinates?.[0]?.[0] ?? []) as [number, number][];
    return ring.filter(
      (p) => Array.isArray(p) && Number.isFinite(p[0]) && Number.isFinite(p[1])
    );
  }
  return [];
}
const FEATURE_SOURCE_NAMES: readonly string[] = Object.values(SOURCES);
function isFeatureSourceName(id: string): id is FeatureSourceName {
  return FEATURE_SOURCE_NAMES.includes(id);
}
function getGmFeatureData(gm: Geoman, sourceId: string, gmId: string): FeatureData | null {
  return isFeatureSourceName(sourceId) ? gm.features.get(sourceId, gmId) : null;
}
function getLayerSource(layer: LayerSpecification): string | undefined {
  return "source" in layer && typeof layer.source === "string" ? layer.source : undefined;
}
function getGmFeatureId(f: GmFeatureIdSource | null | undefined): string | null {
  const candidates = [f?.properties?.__gm_id, f?.id, f?.properties?.client_id]
    .map((v) => (v == null ? null : String(v)))
    .filter((s) => !!s && s !== "undefined" && s !== "null");
  return candidates[0] ?? null;
}
function normalizeToUIPolygon(f: GeoJsonShapeFeature): IntersectionAreaGeoJSON | null {
  const id = getGmFeatureId(f);
  if (!id) return null;
  const name = String(f?.properties?.name ?? "");
  const mode = f?.properties?.mode as "entry" | "reserve" | undefined;
  const priority = f?.properties?.priority as number | undefined;
  const geom = f?.geometry;
  const ring = sanitizeRing(
    extractOuterRing(geom?.type === "Polygon" || geom?.type === "MultiPolygon" ? geom : null)
  );
  if (ring.length < 3) return null;
  return {
    type: "Feature",
    properties: { name, gm_id: id, mode, priority },
    geometry: { type: "Polygon", coordinates: [ring] },
  };
}
function toLatLngListFromRing(ring: [number, number][]): number[][] {
  return (ring ?? []).map(([lng, lat]) => [lat, lng]);
}
const safeUUID = () => {
  try {
    return crypto.randomUUID();
  } catch {
    return `cid_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  }
};
function areasToFeatureCollection(
  areas: Area[],
  mode: "entry" | "reserve"
): GeoJsonImportFeatureCollection {
  return {
    type: "FeatureCollection",
    features: (areas ?? []).map((a): GeoJsonImportFeature => {
      const ringLngLat = (a.vertex_list ?? []).map(
        ([lat, lng]) => [lng, lat] as [number, number]
      );
      const closed = ensureClosedRing(ringLngLat);
      const clientId = safeUUID();
      const props: IntersectionAreaProps = {
        name: a.name,
        mode,
        priority: mode === "reserve" ? a.priority : undefined,
      };
      return {
        type: "Feature",
        id: clientId,
        properties: { ...props, client_id: clientId },
        geometry: { type: "Polygon", coordinates: [closed] },
      };
    }),
  };
}
const isNonEmptyString = (v: unknown): v is string =>
  typeof v === "string" && v.length > 0;

function roundRing(ring: [number, number][]): [number, number][] {
  const round6 = (num: number) => Math.round(num * 1e6) / 1e6;
  return ring.map(([lng, lat]) => [round6(lng), round6(lat)]);
}

const z2hDigits = (s: string) =>
  s.replace(/[０-９]/g, (d) => String.fromCharCode(d.charCodeAt(0) - 0xFEE0));

/** prefix の後ろが「数字だけ」のときだけ使用済み番号としてカウント */
function numberFromName(nm: string, prefix: string): number | null {
  const t = z2hDigits((nm || "").trim());
  if (!t.startsWith(prefix)) return null;
  const tail = t.slice(prefix.length).trim();
  const m = tail.match(/^(\d+)$/);   // ← “数字のみ” にマッチ
  return m ? Number(m[1]) : null;
}

export default function IntersectionDraw({
  onChange,
  initialShapes,
}: IntersectionDrawProps) {
  const { current: mapRef } = useMap();
  const t = useTranslations("Config");
  const prefix = t("area.prefix");

  // ---- States ----
  const [entryShapes, setEntryShapes] = useState<IntersectionAreaGeoJSON[]>([]);
  const [reserveShapes, setReserveShapes] = useState<IntersectionAreaGeoJSON[]>(
    []
  );
  const [selectedMode, setSelectedMode] =
    useState<"entry" | "reserve">("entry");
  const selectedModeRef = useRef<"entry" | "reserve">(selectedMode);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // ---- Refs ----
  const gmRef = useRef<Geoman | null>(null);
  const shapesRef = useRef<IntersectionAreaGeoJSON[]>([]);
  const gmSourceIdRef = useRef<string | null>(null);
  const gmLayerIdsRef = useRef<string[]>([]);
  const readyRef = useRef<boolean>(false);
  const initOnceRef = useRef<boolean>(false);
  const currentNamesRef = useRef<Map<string, string>>(new Map());
  const currentModesRef = useRef<Map<string, "entry" | "reserve">>(new Map());

  // backup
  const lastGoodFcRef = useRef<GeoJsonShapeFeatureCollection | null>(null);
  const suppressRehydrateOnceRef = useRef<boolean>(false);

  // 最新 shapes を常に参照
  const allShapes = useMemo(
    () => [...entryShapes, ...reserveShapes],
    [entryShapes, reserveShapes]
  );
  useEffect(() => {
    shapesRef.current = allShapes;
  }, [allShapes]);

  // トグル同期
  useEffect(() => {
    selectedModeRef.current = selectedMode;
  }, [selectedMode]);

  // 名前キャッシュ
  useEffect(() => {
    for (const s of allShapes) {
      const id = s.properties?.gm_id;
      const name = (s.properties?.name ?? "").trim();
      if (id && name) currentNamesRef.current.set(id, name);
    }
  }, [allShapes]);

  // ---- 自動補完（空だけ埋める）----
  const fillMissingNamesPerMode = useCallback(
    (arr: IntersectionAreaGeoJSON[], mode: "entry" | "reserve") => {
      // 既存の番号を使用済みとして確保
      const used = new Set<number>();
      const siblings = mode === "entry" ? entryShapes : reserveShapes;
      for (const s of siblings) {
        const n = numberFromName(s?.properties?.name ?? "", prefix);
        if (n != null) used.add(n);
      }
      const nextAvailable = () => {
        let i = 1;
        while (used.has(i)) i++;
        used.add(i);
        return i;
      };

      return (arr ?? []).map((f) => {
        let name = (f.properties?.name ?? "").trim();

        // キャッシュから救済
        if (!name && f.properties?.gm_id) {
          const cached = currentNamesRef.current.get(f.properties.gm_id);
          if (cached) name = cached;
        }

        // それでも空なら"一度だけ"採番
        if (!name) name = `${prefix} ${nextAvailable()}`;

        // reserve の priority は未設定なら 1
        const pr =
          mode === "reserve"
            ? (typeof f.properties?.priority === "number"
                ? f.properties.priority
                : 1)
            : undefined;

        const ring = (f.geometry?.coordinates?.[0] ?? []) as [number, number][];
        const rounded = roundRing(ring);

        return {
          ...f,
          properties: { ...f.properties, name, mode, priority: pr },
          geometry: { ...f.geometry, coordinates: [rounded] },
        };
      });
    },
    [prefix, entryShapes, reserveShapes]
  );

  // ---- Geoman Export -> UI 読み取り ----
  const readFromGeoman = useCallback((): IntersectionAreaGeoJSON[] => {
    const gm = gmRef.current;
    if (!gm) return [];
    const exported = gm.features.exportGeoJson({ idPropertyName: "__gm_id" });

    if (exported && (exported.features?.length ?? 0) > 0) {
      lastGoodFcRef.current = exported;
    }

    const acc: IntersectionAreaGeoJSON[] = [];
    for (const f of exported?.features ?? []) {
      const ui = normalizeToUIPolygon(f);
      if (ui) acc.push(ui);
    }
    return acc;
  }, []);

  // ---- Geoman import（id 指定で差分上書き）----
  const importUpdateByGmId = useCallback(
    (gmId: string, patch: GeomanFeaturePatch = {}) => {
      const gm = gmRef.current;
      if (!gm || !gmId) return;

      let geometry = patch.geometry ?? null;
      let baseProps: Record<string, unknown> | null = null;

      try {
        const exported = gm.features.exportGeoJson({ idPropertyName: "__gm_id" });
        const found = (exported?.features ?? []).find(
          (f) => getGmFeatureId(f) === gmId
        );
        if (found) {
          if (!geometry) geometry = found?.geometry ?? null;
          baseProps = { ...(found?.properties ?? {}) };
        }
      } catch {}

      if (!geometry || !geometry.type || !baseProps) {
        const s = shapesRef.current.find((x) => x?.properties?.gm_id === gmId);
        if (s) {
          const ring = (s?.geometry?.coordinates?.[0] ?? []) as [number, number][];
          if ((!geometry || !geometry.type) && Array.isArray(ring) && ring.length >= 3) {
            geometry = { type: "Polygon", coordinates: [ensureClosedRing(ring)] };
          }
          if (!baseProps) {
            baseProps = { ...(s.properties ?? {}) };
          }
        }
      }

      if (!geometry || !geometry.type) return;

      const finalProps: ImportGeoJsonProperties = {
        ...(baseProps ?? {}),
        ...(patch.properties ?? {}),
        __gm_id: gmId,
      };

      if (!finalProps.mode) {
        const cachedMode = currentModesRef.current.get(gmId);
        finalProps.mode = cachedMode ?? selectedModeRef.current; // 最後はトグルのモードで救済
      }
      if (!finalProps.name) {
        const cachedName = currentNamesRef.current.get(gmId);
        if (cachedName) finalProps.name = cachedName;
      }
      if (finalProps.mode === "reserve") {
        finalProps.priority = typeof finalProps.priority === "number" ? finalProps.priority : 1;
      } else {
        // entry なら priority は不要
        if ("priority" in finalProps) delete finalProps.priority;
      }

      const fc: GeoJsonImportFeatureCollection = {
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            properties: finalProps,
            geometry,
          },
        ],
      };

      try {
        gm.features.importGeoJson(fc, {
          idPropertyName: "__gm_id",
          overwrite: true,
        });
      } catch {}
    },
    []
  );

  // ---- GM に差分 persist（name/mode/priority のみ）----
  const persistMissingProps = useCallback(
    (arr: IntersectionAreaGeoJSON[]) => {
      const gm = gmRef.current;
      if (!gm) return;

      const exported = gm.features.exportGeoJson({ idPropertyName: "__gm_id" });
      const byId = new Map<string, GeoJsonShapeFeature>();
      for (const f of exported?.features ?? []) {
        const id = getGmFeatureId(f);
        if (id) byId.set(id, f);
      }

      for (const s of arr) {
        const id = s.properties?.gm_id;
        if (!id) continue;

        const src = byId.get(id);
        const curName = String(src?.properties?.name ?? "").trim();
        const curMode = src?.properties?.mode as
          | "entry"
          | "reserve"
          | undefined;
        const curPrio = src?.properties?.priority as number | undefined;

        const nextName = (s.properties?.name ?? "").toString().trim();
        const nextMode = s.properties?.mode as "entry" | "reserve";
        const nextPrio = s.properties?.priority as number | undefined;

        const needName = nextName && curName !== nextName;
        const needMode = !!nextMode && curMode !== nextMode;
        const needPrio =
          nextMode === "reserve" && curPrio !== (nextPrio ?? 1);

        if (needName || needMode || needPrio) {
          importUpdateByGmId(id, {
            properties: {
              ...(needName ? { name: nextName } : {}),
              ...(needMode ? { mode: nextMode } : {}),
              ...(nextMode === "reserve"
                ? { priority: nextPrio ?? 1 }
                : { priority: undefined }),
            },
          });
        }
      }
    },
    [importUpdateByGmId]
  );

  // すべての図形に name/mode/priority と座標丸めを適用
  const fillAndRoundAll = useCallback(
    (arr: IntersectionAreaGeoJSON[]): IntersectionAreaGeoJSON[] => {
      const usedEntryNums = new Set<number>();
      const usedReserveNums = new Set<number>();

      // モード別に採番状況を先に集計
      const numberFrom = (nm: string): number | null => {
        const t = (nm || "").trim();
        if (!t.startsWith(prefix)) return null;
        const n = parseInt(t.slice(prefix.length).trim(), 10);
        return Number.isFinite(n) ? n : null;
      };

      for (const s of entryShapes) {
        const n = numberFrom(s?.properties?.name ?? "");
        if (n != null) usedEntryNums.add(n);
      }
      for (const s of reserveShapes) {
        const n = numberFrom(s?.properties?.name ?? "");
        if (n != null) usedReserveNums.add(n);
      }

      const nextNumber = (set: Set<number>) => {
        let i = 1;
        while (set.has(i)) i++;
        set.add(i);
        return i;
      };

      return (arr ?? []).map((f) => {
        const id = f.properties?.gm_id!;
        // mode 補完：GM → 既存記憶 → トグル
        let mode = (f.properties?.mode as "entry" | "reserve" | undefined)
                ?? currentModesRef.current.get(id)
                ?? selectedModeRef.current;

        // name 補完：GM → 記憶 → 採番
        let name = (f.properties?.name ?? "").trim();
        if (!name && id) {
          const cached = currentNamesRef.current.get(id);
          if (cached) name = cached;
        }
        if (!name) {
          const set = mode === "reserve" ? usedReserveNums : usedEntryNums;
          name = `${prefix} ${nextNumber(set)}`;
        }

        // priority 補完（reserve のみ）
        const pr =
          mode === "reserve"
            ? (typeof f.properties?.priority === "number" ? f.properties.priority : 1)
            : undefined;

        // 座標は丸めて UI に保持
        const ring = (f.geometry?.coordinates?.[0] ?? []) as [number, number][];
        const rounded = roundRing(ring);

        // キャッシュ更新
        currentNamesRef.current.set(id, name);
        currentModesRef.current.set(id, mode);

        return {
          ...f,
          properties: { ...f.properties, name, mode, priority: pr },
          geometry: { ...f.geometry, coordinates: [rounded] },
        };
      });
    },
    [prefix, entryShapes, reserveShapes]
  );

  // refresh: まず全部読み取り → 補完 → 分割 → GM へ不足プロパティ persist
  const refreshWithRetry = useCallback(async () => {
    const all = readFromGeoman();
    const fixedAll = fillAndRoundAll(all);

    const entries = fixedAll.filter((f) => f.properties?.mode === "entry");
    const reserves = fixedAll.filter((f) => f.properties?.mode === "reserve");

    setEntryShapes(entries);
    setReserveShapes(reserves);

    // GM 側へ属性の不足分を確定反映（name/mode/priority すべて）
    persistMissingProps(fixedAll);
  }, [readFromGeoman, fillAndRoundAll, persistMissingProps]);

  const syncAfterImport = useCallback(async () => {
    for (let i = 0; i < 20; i++) {
      const all = readFromGeoman();
      if (all.length > 0) {
        try {
          const gm = gmRef.current;
          const exported = gm?.features?.exportGeoJson?.({
            idPropertyName: "__gm_id",
          });
          if (exported && (exported.features?.length ?? 0) > 0) {
            lastGoodFcRef.current = exported;
          }
        } catch {}
        const entries = all.filter((f) => f.properties?.mode === "entry");
        const reserves = all.filter((f) => f.properties?.mode === "reserve");

        const filledEntry = fillMissingNamesPerMode(entries, "entry");
        const filledReserve = fillMissingNamesPerMode(reserves, "reserve");

        setEntryShapes(filledEntry);
        setReserveShapes(filledReserve);
        persistMissingProps([...filledEntry, ...filledReserve]);
        return;
      }
      await new Promise((r) => setTimeout(r, 30));
    }
    const all = readFromGeoman();
    const entries = all.filter((f) => f.properties?.mode === "entry");
    const reserves = all.filter((f) => f.properties?.mode === "reserve");

    const filledEntry = fillMissingNamesPerMode(entries, "entry");
    const filledReserve = fillMissingNamesPerMode(reserves, "reserve");

    setEntryShapes(filledEntry);
    setReserveShapes(filledReserve);
    persistMissingProps([...filledEntry, ...filledReserve]);

    try {
      const gm = gmRef.current;
      const exported = gm?.features?.exportGeoJson?.({
        idPropertyName: "__gm_id",
      });
      if (exported && (exported.features?.length ?? 0) > 0) {
        lastGoodFcRef.current = exported;
      }
    } catch {}
  }, [readFromGeoman, fillMissingNamesPerMode, persistMissingProps]);

  // ---- UI -> GM: 座標適用 ----
  const applyCoordsToFeature = useCallback(
    (gmId: string, coords: [number, number][]) => {
      const uiRing = sanitizeRing(coords);
      const closed = ensureClosedRing(uiRing);
      importUpdateByGmId(gmId, {
        geometry: { type: "Polygon", coordinates: [closed] },
      });

      setTimeout(() => {
        refreshWithRetry();
      }, 30);
    },
    [importUpdateByGmId, refreshWithRetry]
  );

  // ---- UI -> GM: 削除 ----
  const removeFeatureById = useCallback(
    (gmId: string) => {
      suppressRehydrateOnceRef.current = true;
      const gm = gmRef.current;
      if (gm) {
        try {
          const srcId = gmSourceIdRef.current ?? GM_SOURCE_ID_FALLBACK;
          const fd = getGmFeatureData(gm, srcId, gmId);
          if (fd?.delete) {
            fd.delete();
          } else {
            const exported = gm.features.exportGeoJson({
              idPropertyName: "__gm_id",
            });
            const filtered: GeoJsonImportFeatureCollection = {
              type: "FeatureCollection",
              features: (exported?.features ?? []).filter(
                (f) => getGmFeatureId(f) !== gmId
              ),
            };
            gm.features.importGeoJson(filtered, {
              idPropertyName: "__gm_id",
              overwrite: true,
            });
          }
        } catch {}
      }

      try {
        const gm = gmRef.current;
        const exp = gm?.features?.exportGeoJson?.({ idPropertyName: "__gm_id" });
        if (exp) lastGoodFcRef.current = exp;
      } catch {}

      setEntryShapes((prev) => prev.filter((s) => s.properties.gm_id !== gmId));
      setReserveShapes((prev) =>
        prev.filter((s) => s.properties.gm_id !== gmId)
      );
      // 選択解除
      setSelectedId((cur) => (cur === gmId ? null : cur));

      setTimeout(() => refreshWithRetry(), 30);
    },
    [refreshWithRetry]
  );

  // ---- UI -> GM: 名前反映（モード内で既存名は尊重。衝突時は最小空き番を割当）----
  const commitNameToFeature = useCallback(
    (gmId: string, rawName: string, mode: "entry" | "reserve") => {
      const final = (rawName ?? "").trim();

      if (!final) {
        // 空 → 自動採番（モード内）
        const peers = mode === "entry" ? entryShapes : reserveShapes;
        const used = new Set<number>();
        for (const s of peers) {
          if (s.properties.gm_id === gmId) continue;
          const n = numberFromName(s?.properties?.name ?? "", prefix);
          if (n != null) used.add(n);
        }
        const nextAvailable = () => { let i = 1; while (used.has(i)) i++; return i; };
        const fallback = `${prefix} ${nextAvailable()}`;

        importUpdateByGmId(gmId, { properties: { name: fallback } });
        currentNamesRef.current.set(gmId, fallback);

        if (mode === "entry") {
          setEntryShapes((prev) =>
            prev.map((s) =>
              s.properties.gm_id === gmId
                ? { ...s, properties: { ...s.properties, name: fallback } }
                : s
            )
          );
        } else {
          setReserveShapes((prev) =>
            prev.map((s) =>
              s.properties.gm_id === gmId
                ? { ...s, properties: { ...s.properties, name: fallback } }
                : s
            )
          );
        }
        setTimeout(() => refreshWithRetry(), 30);
        return;
      }

      importUpdateByGmId(gmId, { properties: { name: final } });
      currentNamesRef.current.set(gmId, final);

      if (mode === "entry") {
        setEntryShapes((prev) =>
          prev.map((s) =>
            s.properties.gm_id === gmId
              ? { ...s, properties: { ...s.properties, name: final } }
              : s
          )
        );
      } else {
        setReserveShapes((prev) =>
          prev.map((s) =>
            s.properties.gm_id === gmId
              ? { ...s, properties: { ...s.properties, name: final } }
              : s
          )
        );
      }
      setTimeout(() => refreshWithRetry(), 30);
    },
    [entryShapes, reserveShapes, prefix, importUpdateByGmId, refreshWithRetry]
  );

  // ---- UI -> GM: priority（reserveのみ）----
  const commitPriorityToFeature = useCallback(
    (gmId: string, priority: number | undefined) => {
      importUpdateByGmId(gmId, { properties: { priority } });
      setReserveShapes((prev) =>
        prev.map((s) =>
          s.properties.gm_id === gmId
            ? { ...s, properties: { ...s.properties, priority } }
            : s
        )
      );
      setTimeout(() => refreshWithRetry(), 30);
    },
    [importUpdateByGmId, refreshWithRetry]
  );

  // ---- 親へ通知（準備完了後のみ）----
  useEffect(() => {
    if (!readyRef.current) return;
    const enrich = (arr: IntersectionAreaGeoJSON[]) =>
      arr.map((f) => {
        const ring = (f.geometry?.coordinates?.[0] ?? []) as [number, number][];
        return {
          ...f,
          properties: {
            ...f.properties,
            vertex_list: toLatLngListFromRing(ring),
          },
        };
      });
    onChange({
      entryShapes: enrich(entryShapes),
      reserveShapes: enrich(reserveShapes),
    });
  }, [entryShapes, reserveShapes, onChange]);

  // ---- 初期化 ----
  useEffect(() => {
    if (initOnceRef.current) return;
    initOnceRef.current = true;

    const raw = mapRef?.getMap() as MaplibreMap | undefined;
    if (!raw) return;

    const buttonTitles = {
      draw: t("geoman.buttonTitles.drawPolyButton"),
      edit: t("geoman.buttonTitles.editButton"),
      drag: t("geoman.buttonTitles.dragButton"),
      rotate: t("geoman.buttonTitles.rotateButton"),
      del: t("geoman.buttonTitles.deleteButton"),
      snap: t("geoman.buttonTitles.snappingButton"),
    };

    const gmOptions: GmOptionsPartial = {
      settings: { controlsPosition: "top-left" },
      controls: {
        draw: {
          marker: { uiEnabled: false, active: false },
          circle_marker: { uiEnabled: false, active: false },
          text_marker: { uiEnabled: false, active: false },
          circle: { uiEnabled: false, active: false },
          ellipse: { uiEnabled: false, active: false },
          line: { uiEnabled: false, active: false },
          rectangle: { uiEnabled: false, active: false },
          polygon: { uiEnabled: true, active: false, title: buttonTitles.draw },
        },
        edit: {
          change: { uiEnabled: true, active: false, title: buttonTitles.edit },
          drag: { uiEnabled: true, active: false, title: buttonTitles.drag },
          rotate: { uiEnabled: true, active: false, title: buttonTitles.rotate },
          cut: { uiEnabled: false, active: false },
          delete: { uiEnabled: true, active: false, title: buttonTitles.del },
        },
        helper: {
          snapping: { uiEnabled: true, active: false, title: buttonTitles.snap },
          zoom_to_features: { uiEnabled: false, active: false },
        },
      },
    };

    const rawWithGm = raw as MaplibreMapWithGeoman;
    const gm: Geoman = rawWithGm.gm ?? new Geoman(raw, gmOptions);
    rawWithGm.gm = gm;
    gmRef.current = gm;

    const resolveGmSourceId = () => {
      const style = raw.getStyle();
      if (!style) return null;
      const gmSource = (style.layers ?? [])
        .map(getLayerSource)
        .find((src) => src?.startsWith("gm_"));
      if (gmSource) return gmSource;
      if (raw.getSource(GM_SOURCE_ID_FALLBACK)) return GM_SOURCE_ID_FALLBACK;
      return null;
    };

    const waitForGmMainSource = async (timeout = 3000): Promise<string> => {
      return new Promise((resolve, reject) => {
        const start = Date.now();
        const tick = () => {
          const id = resolveGmSourceId();
          if (id) {
            gmSourceIdRef.current = id;
            return resolve(id);
          }
          if (Date.now() - start > timeout)
            return reject(new Error("GM main source not ready"));
          requestAnimationFrame(tick);
        };
        tick();
      });
    };

    const collectGmLayers = () => {
      const layers = (raw.getStyle()?.layers ?? []) as LayerSpecification[];
      const gmSrc = gmSourceIdRef.current ?? GM_SOURCE_ID_FALLBACK;
      gmLayerIdsRef.current = layers
        .filter((layer) => getLayerSource(layer) === gmSrc)
        .map((l) => l.id);
    };

    const applyGmVisualStyle = () => {
      const layers = (raw.getStyle()?.layers ?? []) as LayerSpecification[];
      const gmMain = gmSourceIdRef.current ?? GM_SOURCE_ID_FALLBACK;
      const dynamicColor = (selectedModeRef.current === "reserve") ? RESERVE_COLOR : ENTRY_COLOR;

      for (const layer of layers) {
        const src = getLayerSource(layer);
        if (!src || !src.startsWith("gm_")) continue;

        if (layer.type === "fill") {
          if (src === gmMain) {
            try {
              // ★ mode による色分け
              raw.setPaintProperty(layer.id, "fill-color", [
                "case",
                ["==", ["get", "mode"], "reserve"],
                RESERVE_COLOR,
                ENTRY_COLOR,
              ]);
              raw.setPaintProperty(layer.id, "fill-opacity", 0.5);
            } catch {}
          } else {
            try {
              raw.setPaintProperty(layer.id, "fill-color", dynamicColor);
              raw.setPaintProperty(layer.id, "fill-opacity", 0.5);
            } catch {}
          }
        } else if (layer.type === "line") {
          try {
            if (src === gmMain) {
              raw.setPaintProperty(layer.id, "line-opacity", 0);
              raw.setPaintProperty(layer.id, "line-width", 0);
            } else {
              raw.setPaintProperty(layer.id, "line-color", dynamicColor);
              raw.setPaintProperty(layer.id, "line-opacity", 1);
              raw.setPaintProperty(layer.id, "line-width", 2);
            }
          } catch {}
        }
      }
      collectGmLayers();
    };

    const withStyleReady = (cb: () => void) => {
      if (raw.isStyleLoaded()) return cb();
      const handler = () => {
        if (raw.isStyleLoaded()) {
          raw.off("styledata", handler);
          cb();
        }
      };
      raw.on("styledata", handler);
    };

    readyRef.current = false;

    withStyleReady(() => {
      (async () => {
        try {
          await waitForGmMainSource();

          // 既存が無ければ initial を import
          let have = 0;
          try {
            const exp0 = gm.features.exportGeoJson({
              idPropertyName: "__gm_id",
            });
            have = exp0?.features?.length ?? 0;
          } catch {}

          if (have === 0 && initialShapes) {
            const fcEntry = areasToFeatureCollection(
              initialShapes.entry_area ?? [],
              "entry"
            );
            const fcReserve = areasToFeatureCollection(
              initialShapes.reserve_area ?? [],
              "reserve"
            );
            const fc: GeoJsonImportFeatureCollection = {
              type: "FeatureCollection",
              features: [
                ...(fcEntry.features ?? []),
                ...(fcReserve.features ?? []),
              ],
            };
            try {
              gm.features.importGeoJson(fc, {
                idPropertyName: "client_id",
                overwrite: true,
              });
            } catch {}
          }

          try {
            const exp = gm.features.exportGeoJson({
              idPropertyName: "__gm_id",
            });
            if ((exp?.features?.length ?? 0) > 0) {
              lastGoodFcRef.current = exp;
            }
          } catch {}

          applyGmVisualStyle();

          await syncAfterImport();

          await new Promise((r) => setTimeout(r, 30));
          refreshWithRetry();
          readyRef.current = true;
        } catch {
          applyGmVisualStyle();
          await syncAfterImport();
          readyRef.current = true;
        }
      })();
    });

    // ---- Events ----
    const onCreate = () => {
      try {
        const gm = gmRef.current;
        const exported = gm?.features.exportGeoJson({
          idPropertyName: "__gm_id",
        });

        // いま地図に存在している ID
        const nowIds = new Set<string>(
          (exported?.features ?? [])
            .map((f) => getGmFeatureId(f))
            .filter(isNonEmptyString)
        );
        // UI に既知の ID
        const prevIds = new Set<string>(
          shapesRef.current
            .map((s) => s.properties?.gm_id)
            .filter(isNonEmptyString)
        );

        // 新規追加分
        const newIds = [...nowIds].filter((id) => !prevIds.has(id));

        // 同モード内の採番
        const peers =
          selectedModeRef.current === "entry" ? entryShapes : reserveShapes;
        const used = new Set<number>();
        const numberFrom = (nm: string): number | null => numberFromName(nm, prefix)
        for (const s of peers) {
          const n = numberFrom(s?.properties?.name ?? "");
          if (n != null) used.add(n);
        }
        const nextAvailable = () => {
          let i = 1;
          while (used.has(i)) i++;
          used.add(i);
          return i;
        };

        for (const id of newIds) {
          const props: IntersectionAreaProps = {
            name: `${prefix} ${nextAvailable()}`,
            mode: selectedModeRef.current,
          };
          if (selectedModeRef.current === "reserve") props.priority = 1;

          // 一回だけ確定
          importUpdateByGmId(id, { properties: props });
          currentNamesRef.current.set(id, props.name);
        }
      } catch {}

      setTimeout(() => refreshWithRetry(), 30);
    };

    const onEditEnd = () => setTimeout(() => refreshWithRetry(), 30);
    const onRemove = () => {
      suppressRehydrateOnceRef.current = true;
      try {
        const gm = gmRef.current;
        const exp = gm?.features?.exportGeoJson?.({ idPropertyName: "__gm_id" });
        if (exp) lastGoodFcRef.current = exp;
      } catch {}
      setTimeout(() => refreshWithRetry(), 30);
    };
    const onDragEnd = () => setTimeout(() => refreshWithRetry(), 30);
    const onRotateEnd = () => setTimeout(() => refreshWithRetry(), 30);

    const gmEventBindings: GmEventBinding[] = [
      ["gm:create", onCreate],
      ["gm:editend", onEditEnd],
      ["gm:remove", onRemove],
      ["gm:dragend", onDragEnd],
      ["gm:rotateend", onRotateEnd],
    ];
    for (const [name, handler] of gmEventBindings) raw.on(name, handler);

    const styleHandler = () => {
      if (!raw.isStyleLoaded()) return;
      gmSourceIdRef.current = resolveGmSourceId();
      applyGmVisualStyle();

      try {
        const gm = gmRef.current;
        const exported = gm?.features?.exportGeoJson?.({
          idPropertyName: "__gm_id",
        });
        const count = exported?.features?.length ?? 0;
        const lastGood = lastGoodFcRef.current;

        if (count === 0 && lastGood && (lastGood.features?.length ?? 0) > 0) {
          if (suppressRehydrateOnceRef.current) {
            suppressRehydrateOnceRef.current = false;
          } else if (gm) {
            gm.features.importGeoJson(lastGood, {
              idPropertyName: "__gm_id",
              overwrite: true,
            });
            setTimeout(() => refreshWithRetry(), 80);
            return;
          }
        }
      } catch {}

      setTimeout(() => refreshWithRetry(), 120);
    };
    raw.on("styledata", styleHandler);

    // cleanup
    return () => {
      for (const [name, handler] of gmEventBindings) raw.off(name, handler);
      raw.off("styledata", styleHandler);
      gmRef.current = null;
      initOnceRef.current = false;
    };
  }, [
    mapRef,
    initialShapes,
    t,
    prefix,
    entryShapes,
    reserveShapes,
    importUpdateByGmId,
    syncAfterImport,
    refreshWithRetry,
  ]);

  useEffect(() => {
    const raw = mapRef?.getMap() as MaplibreMap | undefined;
    if (!raw || !raw.isStyleLoaded()) return;

    const layers = (raw.getStyle()?.layers ?? []) as LayerSpecification[];
    const gmMain = gmSourceIdRef.current ?? GM_SOURCE_ID_FALLBACK;
    const color = selectedMode === "reserve" ? RESERVE_COLOR : ENTRY_COLOR;

    for (const layer of layers) {
      const src = getLayerSource(layer);
      if (!src || !src.startsWith("gm_")) continue;
      if (src === gmMain) continue; // メインは mode プロパティで色が決まるので触らない

      try {
        if (layer.type === "line") {
          raw.setPaintProperty(layer.id, "line-color", color);
          raw.setPaintProperty(layer.id, "line-opacity", 1);
          raw.setPaintProperty(layer.id, "line-width", 2);
        } else if (layer.type === "fill") {
          raw.setPaintProperty(layer.id, "fill-color", color);
          raw.setPaintProperty(layer.id, "fill-opacity", 0.5);
        }
      } catch {}
    }
  }, [selectedMode, mapRef]);

  // 図形クリックで選択、空白クリックで解除
  useEffect(() => {
    const map = mapRef?.getMap();
    if (!map) return;

    const layers = gmLayerIdsRef.current;
    if (!layers || layers.length === 0) return;

    // Geoman のメイン fill layer を想定
    const polyLayerId = layers[0];

    const onPolyClick = (e: MapLayerMouseEvent) => {
      const f = e?.features?.[0];
      if (!f) return;
      const gmId =
        f.properties?.__gm_id || f.properties?.client_id || f.id;
      if (!gmId) return;
      setSelectedId(String(gmId));
    };

    map.on("click", polyLayerId, onPolyClick);

    // 地図の空白クリックで選択解除（gm_レイヤに当たっていれば解除しない）
    const handleMapClick = (e: MapMouseEvent) => {
      const features = map.queryRenderedFeatures(e.point);
      const hit = features.some((f) => {
        const lid = f?.layer?.id;
        return lid && lid.startsWith("gm_");
      });
      if (!hit) {
        setSelectedId(null);
      }
    };
    map.on("click", handleMapClick);

    return () => {
      map.off("click", polyLayerId, onPolyClick);
      map.off("click", handleMapClick);
    };
  }, [mapRef, entryShapes, reserveShapes]);

  // ---- ラベル（名前表示）----
  const labelsGeoJson = useMemo<FeatureCollection>(
    () => ({
      type: "FeatureCollection",
      features: [...entryShapes, ...reserveShapes].map((f) => ({
        type: "Feature",
        id: f.id ?? f.properties.gm_id,
        properties: { name: f.properties.name },
        geometry: f.geometry,
      })),
    }),
    [entryShapes, reserveShapes]
  );

  useEffect(() => {
    const raw = mapRef?.getMap() as MaplibreMap | undefined;
    if (!raw) return;

    if (!raw.getSource(LABEL_SRC_ID)) {
      raw.addSource(LABEL_SRC_ID, { type: "geojson", data: labelsGeoJson });
    }
    if (!raw.getLayer(LABEL_LAYER_ID)) {
      raw.addLayer({
        id: LABEL_LAYER_ID,
        type: "symbol",
        source: LABEL_SRC_ID,
        layout: { "text-field": ["get", "name"], "text-size": 12 },
        paint: {
          "text-color": "#111",
          "text-halo-width": 1,
          "text-halo-color": "#fff",
        },
      });
    }

    return () => {
      try {
        if (raw.getLayer(LABEL_LAYER_ID)) raw.removeLayer(LABEL_LAYER_ID);
        if (raw.getSource(LABEL_SRC_ID)) raw.removeSource(LABEL_SRC_ID);
      } catch {}
    };
  }, [mapRef]);

  useEffect(() => {
    const raw = mapRef?.getMap() as MaplibreMap | undefined;
    const src = raw?.getSource<GeoJSONSource>(LABEL_SRC_ID);
    if (src) {
      src.setData(labelsGeoJson);
    }
  }, [mapRef, labelsGeoJson]);

  return (
    <>
      <Box
        sx={{
          position: "absolute",
          top: 10,
          right: 10,
          zIndex: MAP_Z_INDEX.UI_OVERLAY,
          width: { xs: 250, sm: 340 },
          height: "80%",
          display: "flex",
          flexDirection: "column",
          pointerEvents: "none",
        }}
      >
        {/* 進入エリア一覧 */}
        <IntersectionListPanel
          title={t("intersection.entryListTitle")}
          mode="entry"
          shapes={entryShapes}
          setShapes={setEntryShapes}
          applyCoordsToFeature={applyCoordsToFeature}
          removeFeatureById={removeFeatureById}
          commitNameToFeature={commitNameToFeature}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />

        {/* 予約エリア一覧 */}
        <IntersectionListPanel
          title={t("intersection.reserveListTitle")}
          mode="reserve"
          shapes={reserveShapes}
          setShapes={setReserveShapes}
          applyCoordsToFeature={applyCoordsToFeature}
          removeFeatureById={removeFeatureById}
          commitNameToFeature={commitNameToFeature}
          commitPriorityToFeature={commitPriorityToFeature}
          showPriority
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
      </Box>

      <Box
        sx={{
          position: "absolute",
          bottom: 10,
          right: 10,
          zIndex: MAP_Z_INDEX.UI_OVERLAY,
          width: { xs: 250, sm: 340 },
          height: "10%",
        }}
      >
        <IntersectionAreaModeToggle
          selectedMode={selectedMode}
          onChange={setSelectedMode}
        />
      </Box>
    </>
  );
}