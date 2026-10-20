/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

"use client";
import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useMap } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import "@geoman-io/maplibre-geoman-free/dist/maplibre-geoman.css";
import type { Feature, Polygon, MultiPolygon, FeatureCollection } from "geojson";
import type { Map as MaplibreMap, LayerSpecification } from "maplibre-gl";
import { Geoman, type GmOptionsPartial,} from "@geoman-io/maplibre-geoman-free";
import AreaListPanel from "./AreaListPanel";
import { useTranslations } from "next-intl";


export type Area = {
  name: string;
  vertex_list: number[][];
};
interface MapDrawProps {
  onChange: (shapes: AreaGeoJSON[]) => void;
  initialShapes?: Area[]; // Area形式 [{ name, vertex_list }]
}

type AreaGeoJSONProps = { name: string; gm_id?: string; vertex_list?: number[][] };
export type AreaGeoJSON = Feature<Polygon, AreaGeoJSONProps>;

const GM_SOURCE_ID_FALLBACK = "gm_main";
const EPS = 1e-12;

function sanitizeRing(coords: [number, number][]): [number, number][] {
  if (!Array.isArray(coords) || coords.length < 2) return coords;
  const [fx, fy] = coords[0] ?? [];
  const [lx, ly] = coords[coords.length - 1] ?? [];
  const same = Math.abs((fx ?? 0) - (lx ?? 1e9)) <= EPS && Math.abs((fy ?? 0) - (ly ?? 1e9)) <= EPS;
  return same ? coords.slice(0, -1) : coords;
}
function ensureClosedRing(coords: [number, number][]): [number, number][] {
  if (!Array.isArray(coords) || coords.length === 0) return coords;
  const [fx, fy] = coords[0] ?? [];
  const [lx, ly] = coords[coords.length - 1] ?? [];
  const same = Math.abs((fx ?? 0) - (lx ?? 1e9)) <= EPS && Math.abs((fy ?? 0) - (ly ?? 1e9)) <= EPS;
  return same ? coords : [...coords, [fx, fy]];
}
function extractOuterRing(geom: Polygon | MultiPolygon | null | undefined): [number, number][] {
  if (!geom) return [];
  if (geom.type === "Polygon") {
    const ring = (geom.coordinates?.[0] ?? []) as [number, number][];
    return ring.filter((p) => Array.isArray(p) && Number.isFinite(p[0]) && Number.isFinite(p[1]));
  }
  if (geom.type === "MultiPolygon") {
    const ring = (geom.coordinates?.[0]?.[0] ?? []) as [number, number][];
    return ring.filter((p) => Array.isArray(p) && Number.isFinite(p[0]) && Number.isFinite(p[1]));
  }
  return [];
}
function getGmFeatureId(f: any): string | null {
  const candidates = [f?.properties?.__gm_id, f?.id, f?.properties?.client_id]
    .map((v) => (v == null ? null : String(v)))
    .filter((s) => !!s && s !== "undefined" && s !== "null");
  return candidates[0] ?? null;
}
function normalizeToUIPolygon(f: any): AreaGeoJSON | null {
  const id = getGmFeatureId(f);
  if (!id) return null;
  const name = (f?.properties?.name ?? "").toString();
  const ring = sanitizeRing(extractOuterRing(f?.geometry));
  if (ring.length < 3) return null;
  return {
    type: "Feature",
    properties: { name, gm_id: id },
    geometry: { type: "Polygon", coordinates: [ring] },
  } as AreaGeoJSON;
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
function areasToFeatureCollection(areas: Area[]): FeatureCollection {
  return {
    type: "FeatureCollection",
    features: (areas ?? []).map((a) => {
      const ringLngLat = (a.vertex_list ?? []).map(([lat, lng]) => [lng, lat] as [number, number]);
      const closed = ensureClosedRing(ringLngLat);
      const clientId = safeUUID();
      return {
        type: "Feature",
        id: clientId, // Top-level id（保険）
        properties: { name: a.name, client_id: clientId },
        geometry: { type: "Polygon", coordinates: [closed] },
      } as Feature;
    }),
  } as FeatureCollection;
}

function roundRing(ring: [number, number][]): [number, number][] {
  const round6 = (num: number) => Math.round(num * 1e6) / 1e6;
  return ring.map(([lng, lat]) => [
    round6(lng),
    round6(lat)
  ]);
}

export default function MapDraw({ onChange, initialShapes = [] }: MapDrawProps) {
  const { current: mapRef } = useMap();
  const [shapes, setShapes] = useState<AreaGeoJSON[]>([]);
  const [selectedAreaId, setSelectedAreaId] = useState<string | null>(null);
  const gmRef = useRef<Geoman | null>(null);
  const translate = useTranslations("Config");
  const prefix = translate("area.prefix");

  // 最新の shapes を常に参照できるようにする（import 時の geometry フォールバック用）
  const shapesRef = useRef<AreaGeoJSON[]>([]);
  useEffect(() => {
    shapesRef.current = shapes;
  }, [shapes]);

  // GM ソース/レイヤ
  const gmSourceIdRef = useRef<string | null>(null);
  const gmLayerIdsRef = useRef<string[]>([]);

  // 名前キャッシュ & 親通知ガード & 初期化ワンショット
  const currentNamesRef = useRef<Map<string, string>>(new Map());
  const readyRef = useRef<boolean>(false);
  const initOnceRef = useRef<boolean>(false); // StrictMode対策：初期化は1回

  // “良い状態”のバックアップ（空読み時の自己復元に使用）
  const lastGoodFcRef = useRef<FeatureCollection | null>(null);
  const suppressRehydrateOnceRef = useRef<boolean>(false);

  /** 名前キャッシュ更新 */
  useEffect(() => {
    for (const s of shapes) {
      const id = String(s.properties?.gm_id ?? "");
      const nm = s.properties?.name?.trim();
      if (id && nm) currentNamesRef.current.set(id, nm);
    }
  }, [shapes]);

  /** 名前の穴埋め＆連番採番（UI側） */
  const ensureNames = useCallback(
    (arr: AreaGeoJSON[]): AreaGeoJSON[] => {
      const used = new Set<number>();
      const z2hDigits = (s: string) =>
        s.replace(/[０-９]/g, (d) => String.fromCharCode(d.charCodeAt(0) - 0xFEE0));
      const nameToNum = (nm: string) => {
        const t = (nm || "").trim();
        if (!t.startsWith(prefix)) return NaN;
        const tailRaw = t.slice(prefix.length).trim();
        const tail = z2hDigits(tailRaw); // 全角→半角（全角を使わないならこの行は不要）

        const m = tail.match(/^(\d+)$/);
        return m ? Number(m[1]) : NaN;
      };
      for (const f of arr) {
        const n = nameToNum(f.properties?.name ?? "");
        if (Number.isFinite(n)) used.add(n as number);
      }
      const nextNumber = () => {
        let i = 1;
        while (used.has(i)) i++;
        used.add(i);
        return i;
      };
      return arr.map((f) => {
        const id = String(f.properties?.gm_id ?? "");
        let name = f.properties?.name?.trim();
        if (!name && id && currentNamesRef.current.has(id)) {
          name = currentNamesRef.current.get(id)!;
        }
        if (!name || name.length === 0) {
          name = `${prefix} ${nextNumber()}`;
        }
        if (id && name) currentNamesRef.current.set(id, name);
        return { ...f, properties: { ...f.properties, name } };
      });
    },
    [prefix]
  );

  /** Geoman -> UI 読み取り（非空時はバックアップ更新） */
  const readFromGeoman = useCallback((): AreaGeoJSON[] => {
    const gm = gmRef.current;
    if (!gm) return [];
    const exported = gm.features.exportGeoJson({ idPropertyName: "__gm_id" });

    if ((exported?.features?.length ?? 0) > 0) {
      lastGoodFcRef.current = exported as unknown as FeatureCollection;
    }

    const acc: AreaGeoJSON[] = [];
    for (const f of (exported?.features ?? []) as any[]) {
      const ui = normalizeToUIPolygon(f);
      if (ui) acc.push(ui);
    }
    return acc;
  }, []);

  /** -------- Geoman 更新のための共通関数（import 上書き） -------- */
  const importUpdateByGmId = useCallback(
    (gmId: string, patch: { geometry?: any; properties?: any } = {}) => {
      const gm = gmRef.current as any;
      if (!gm || !gmId) return;

      let geometry = patch.geometry ?? null;

      // 1) GM 側からフォールバック
      if (!geometry) {
        try {
          const exported = gm.features.exportGeoJson({ idPropertyName: "__gm_id" });
          const found = (exported?.features ?? []).find((f: any) => getGmFeatureId(f) === gmId);
          geometry = found?.geometry ?? null;
        } catch {}
      }

      // 2) UI（shapesRef）からフォールバック
      if (!geometry) {
        const s = shapesRef.current.find((x) => x?.properties?.gm_id === gmId);
        const ring = (s?.geometry?.coordinates?.[0] ?? []) as [number, number][];
        if (Array.isArray(ring) && ring.length >= 3) {
          geometry = { type: "Polygon", coordinates: [ensureClosedRing(ring)] };
        }
      }

      // 3) それでも無いなら安全にスキップ（少なくとも名前キャッシュは保持）
      if (!geometry || !geometry.type) {
        const nm = (patch.properties?.name ?? "").toString().trim();
        if (nm) currentNamesRef.current.set(gmId, nm);
        return;
      }

      const fc = {
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            properties: { __gm_id: gmId, ...(patch.properties ?? {}) },
            geometry,
          },
        ],
      };

      try {
        gm.features.importGeoJson(fc, { idPropertyName: "__gm_id", overwrite: true });
      } catch {}
    },
    []
  );

  /** -------- 命名の確定保存（UI -> Geoman へ同期） -------- */
  const persistMissingNames = useCallback((arr: AreaGeoJSON[]) => {
    const gm = gmRef.current as any;
    if (!gm) return;
    try {
      const exported = gm.features.exportGeoJson({ idPropertyName: "__gm_id" });
      const byId = new Map<string, any>();
      for (const f of (exported?.features ?? []) as any[]) {
        const id = getGmFeatureId(f);
        if (id) byId.set(id, f);
      }
      for (const s of arr) {
        const id = s.properties.gm_id;
        const nm = (s.properties.name ?? "").trim();
        if (!id || !nm) continue;
        const raw = byId.get(id);
        const rawName = (raw?.properties?.name ?? "").toString().trim();
        if (rawName !== nm) {
          importUpdateByGmId(id, { properties: { name: nm } });
        }
      }
    } catch {}
  }, [importUpdateByGmId]);

  /** 小リトライ + 空上書き抑止 + 自己復元 */
  const refreshWithRetry = useCallback(
    async () => {
      const arrRaw = ensureNames(readFromGeoman());
      const arr = arrRaw.map(f => {
        const ring = (f.geometry?.coordinates?.[0] ?? []) as [number, number][];
        const rounded = roundRing(ring);
        return {
          ...f,
          geometry: { ...f.geometry, coordinates: [rounded] }
        };
      });
      const shouldSkipRehydrate = suppressRehydrateOnceRef.current;
      if (shouldSkipRehydrate) suppressRehydrateOnceRef.current = false;
      setShapes(arr);
      persistMissingNames(arr);
    },
    [readFromGeoman, ensureNames, persistMissingNames]
  );

  /** import 後の確定待ち（最後にバックアップ更新） */
  const syncAfterImport = useCallback(async () => {
    for (let i = 0; i < 20; i++) {
      const arrRaw = ensureNames(readFromGeoman());
      const arr = arrRaw.map(f => {
        const ring = (f.geometry?.coordinates?.[0] ?? []) as [number, number][];
        const rounded = roundRing(ring);
        return {
          ...f,
          geometry: { ...f.geometry, coordinates: [rounded] }
        };
      });
      if (arr.length > 0) {
        setShapes(arr);
        persistMissingNames(arr);
        try {
          const gm = gmRef.current as any;
          const exported = gm?.features?.exportGeoJson?.({ idPropertyName: "__gm_id" });
          if ((exported?.features?.length ?? 0) > 0) {
            lastGoodFcRef.current = exported as unknown as FeatureCollection;
          }
        } catch {}
        return;
      }
      await new Promise((r) => setTimeout(r, 30));
    }
    const last = ensureNames(readFromGeoman());
    setShapes(last);
    persistMissingNames(last);
    try {
      const gm = gmRef.current as any;
      const exported = gm?.features?.exportGeoJson?.({ idPropertyName: "__gm_id" });
      if ((exported?.features?.length ?? 0) > 0) {
        lastGoodFcRef.current = exported as unknown as FeatureCollection;
      }
    } catch {}
  }, [readFromGeoman, ensureNames, persistMissingNames]);

  /** 一覧 -> 地図へ座標反映（import 上書き） */
  const applyCoordsToFeature = useCallback(
    (gmId: string, coords: [number, number][]) => {
      const uiRing = sanitizeRing(coords);
      const closed = ensureClosedRing(uiRing);

      setShapes((prev) =>
        prev.map((s) =>
          s.properties.gm_id === gmId
            ? { ...s, geometry: { ...s.geometry, coordinates: [uiRing] } }
            : s
        )
      );

      // Geomanへ確実に反映（import上書き）
      importUpdateByGmId(gmId, {
        geometry: { type: "Polygon", coordinates: [closed] },
      });

      setTimeout(() => refreshWithRetry(), 30);
    },
    [refreshWithRetry, importUpdateByGmId]
  );

  /** 削除（import フォールバック付き） */
  const removeFeatureById = useCallback(
    (gmId: string) => {
      suppressRehydrateOnceRef.current = true;
      const gm = gmRef.current as any;
      if (gm) {
        try {
          const srcId = (gmSourceIdRef.current ?? GM_SOURCE_ID_FALLBACK) as any;
          const fd = gm.features.get?.(srcId, gmId as any);
          if (fd?.delete) {
            fd.delete();
          } else {
            // フォールバック：全体を出して当該IDを除外して再import
            const exported = gm.features.exportGeoJson({ idPropertyName: "__gm_id" });
            const filtered = {
              type: "FeatureCollection",
              features: (exported?.features ?? []).filter((f: any) => getGmFeatureId(f) !== gmId),
            };
            gm.features.importGeoJson(filtered, { idPropertyName: "__gm_id", overwrite: true });
          }
        } catch {}
      }
      setShapes((prev) => prev.filter((s) => s.properties.gm_id !== gmId));
      setTimeout(() => refreshWithRetry(), 30);
    },
    [refreshWithRetry]
  );

  /** 名前反映（UI と GM 双方） — 命名規則を厳密適用、重複は最小空き番に再採番 */
  const commitNameToFeature = useCallback(
    (gmId: string, rawName: string) => {
      const finalName = (rawName ?? "").trim();
      if (!finalName) {
        // 空は補完（既存名があれば維持／無ければプレフィックス + 通番）
        const fallback =
          currentNamesRef.current.get(gmId) ||
          `${prefix} ${(() => {
            const used = new Set<number>();
            for (const s of shapesRef.current) {
              const t = (s?.properties?.name ?? "").trim();
              if (!t.startsWith(prefix)) continue;
              const n = parseInt(t.slice(prefix.length).trim(), 10);
              if (Number.isFinite(n)) used.add(n);
            }
            let i = 1;
            while (used.has(i)) i++;
            return i;
          })()}`;
        // UI だけ更新して終了（GM 側への更新もしておく）
        setShapes(prev =>
          prev.map(s =>
            s.properties.gm_id === gmId
              ? { ...s, properties: { ...s.properties, name: fallback } }
              : s
          )
        );
        try {
          const gm = gmRef.current as any;
          const srcId = gmSourceIdRef.current ?? GM_SOURCE_ID_FALLBACK;
          const fd = gm?.features?.get?.(srcId as any, gmId as any);
          if (fd && typeof fd.setProperties === "function") {
            fd.setProperties({ ...(fd.getProperties?.() ?? {}), name: fallback });
          } else {
            const me = shapesRef.current.find(s => s.properties.gm_id === gmId);
            const ring = ensureClosedRing(
              sanitizeRing((me?.geometry?.coordinates?.[0] ?? []) as [number, number][])
            );
            importUpdateByGmId(gmId, {
              properties: { name: fallback },
              geometry: { type: "Polygon", coordinates: [ring] },
            });
          }
        } catch {}
        setTimeout(() => refreshWithRetry(), 30);
        return;
      }

      // UI を即時更新
      setShapes((prev) =>
        prev.map((s) =>
          s.properties.gm_id === gmId
            ? { ...s, properties: { ...s.properties, name: finalName } }
            : s
        )
      );

      // Geoman側も更新（インプレース優先 → だめなら import フォールバック）
      try {
        const gm = gmRef.current as any;
        const srcId = gmSourceIdRef.current ?? GM_SOURCE_ID_FALLBACK;
        const fd = gm?.features?.get?.(srcId as any, gmId as any);
        if (fd && typeof fd.setProperties === "function") {
          fd.setProperties({ ...(fd.getProperties?.() ?? {}), name: finalName });
        } else {
          const me = shapesRef.current.find(s => s.properties.gm_id === gmId);
          const ring = ensureClosedRing(
            sanitizeRing((me?.geometry?.coordinates?.[0] ?? []) as [number, number][])
          );
          importUpdateByGmId(gmId, {
            properties: { name: finalName },
            geometry: { type: "Polygon", coordinates: [ring] },
          });
        }
      } catch {
        const me = shapesRef.current.find(s => s.properties.gm_id === gmId);
        const ring = ensureClosedRing(
          sanitizeRing((me?.geometry?.coordinates?.[0] ?? []) as [number, number][])
        );
        importUpdateByGmId(gmId, {
          properties: { name: finalName },
          geometry: { type: "Polygon", coordinates: [ring] },
        });
      }

      setTimeout(() => refreshWithRetry(), 30);
    },
    [refreshWithRetry, importUpdateByGmId, prefix, setShapes]
  );

  /** 親へ通知（準備完了後のみ） */
  useEffect(() => {
    if (!readyRef.current) return;
    const enriched: AreaGeoJSON[] = shapes.map((f) => {
      const ring = (f.geometry?.coordinates?.[0] ?? []) as [number, number][];
      return {
        ...f,
        properties: { ...f.properties, vertex_list: toLatLngListFromRing(ring) },
      };
    });
    onChange(enriched);
  }, [shapes, onChange]);

  /** 初期化（ワンショット & 読み取り中心・削除しない） */
  useEffect(() => {
    if (initOnceRef.current) return;
    initOnceRef.current = true;

    const raw = mapRef?.getMap() as MaplibreMap | undefined;
    if (!raw) return;

    const buttonTitles = {
      draw: translate("geoman.buttonTitles.drawPolyButton"),
      edit: translate("geoman.buttonTitles.editButton"),
      drag: translate("geoman.buttonTitles.dragButton"),
      rotate: translate("geoman.buttonTitles.rotateButton"),
      del: translate("geoman.buttonTitles.deleteButton"),
      snap: translate("geoman.buttonTitles.snappingButton"),
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
          drag:   { uiEnabled: true, active: false, title: buttonTitles.drag },
          rotate: { uiEnabled: true, active: false, title: buttonTitles.rotate },
          cut:    { uiEnabled: false, active: false },
          delete: { uiEnabled: true, active: false, title: buttonTitles.del },
        },
        helper: {
          snapping: { uiEnabled: true, active: false, title: buttonTitles.snap },
          zoom_to_features: { uiEnabled: false, active: false },
        },
      },
    };

    let gm: Geoman | null = (raw as any).gm ?? null;
    if (!gm) {
      gm = new Geoman(raw, gmOptions);
      (raw as any).gm = gm;
    }
    gmRef.current = gm;

    const resolveGmSourceId = () => {
      const style = raw.getStyle();
      if (!style) return null;
      const layer = (style.layers ?? []).find(
        (l: any) => typeof l?.source === "string" && (l.source as string).startsWith("gm_")
      ) as any;
      if (layer && typeof layer.source === "string") return layer.source as string;
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
          if (Date.now() - start > timeout) return reject(new Error("GM main source not ready"));
          requestAnimationFrame(tick);
        };
        tick();
      });
    };

    const collectGmLayers = () => {
      const layers = (raw.getStyle()?.layers ?? []) as LayerSpecification[];
      const gmSrc = gmSourceIdRef.current ?? GM_SOURCE_ID_FALLBACK;
      gmLayerIdsRef.current = layers.filter((layer) => (layer as any).source === gmSrc).map((l) => l.id);
    };
    const applyGmVisualStyle = () => {
      const layers = (raw.getStyle()?.layers ?? []) as LayerSpecification[];
      const gmMain = gmSourceIdRef.current ?? GM_SOURCE_ID_FALLBACK;
      for (const layer of layers) {
        const src = (layer as any).source as string | undefined;
        if (!src || !src.startsWith("gm_")) continue;

        if (layer.type === "fill") {
          // メイン（確定図形）の塗りのみ青
          if (src === gmMain) {
            try {
              raw.setPaintProperty(layer.id, "fill-color", "#3388ff");
              raw.setPaintProperty(layer.id, "fill-opacity", 0.5);
            } catch {}
          }
        } else if (layer.type === "line") {
          // メインの枠線は透明、描画/編集ヘルパーは青
          try {
            if (src === gmMain) {
              raw.setPaintProperty(layer.id, "line-opacity", 0);
              raw.setPaintProperty(layer.id, "line-width", 0);
            } else {
              raw.setPaintProperty(layer.id, "line-color", "#3388ff");
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

          // 既に図形がある場合は import しない（重複回避）
          let have = 0;
          try {
            const exp0 = (gm as any).features.exportGeoJson({ idPropertyName: "__gm_id" });
            have = exp0?.features?.length ?? 0;
          } catch {}

          if (have === 0 && (initialShapes?.length ?? 0) > 0) {
            const fc = areasToFeatureCollection(initialShapes ?? []);
            try {
              (gm as any).features.importGeoJson(fc as any, {
                idPropertyName: "client_id",
                overwrite: true,
              });
            } catch {}
          }

          try {
            const exp = (gm as any).features.exportGeoJson({ idPropertyName: "__gm_id" });
            if ((exp?.features?.length ?? 0) > 0) {
              lastGoodFcRef.current = exp as unknown as FeatureCollection;
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

    // ---- イベント同期 ----
    const onCreate   = () => setTimeout(() => refreshWithRetry(), 30);
    const onEditEnd  = () => setTimeout(() => refreshWithRetry(), 30);
    const onRemove   = () => { suppressRehydrateOnceRef.current = true; setTimeout(() => refreshWithRetry(), 30); };
    // ★ 追加：移動/回転でも常に同期
    const onDragEnd  = () => setTimeout(() => refreshWithRetry(), 30);
    const onRotateEnd= () => setTimeout(() => refreshWithRetry(), 30);

    (raw as any).on("gm:create",   onCreate);
    (raw as any).on("gm:editend",  onEditEnd);
    (raw as any).on("gm:remove",   onRemove);
    (raw as any).on("gm:dragend",  onDragEnd);
    (raw as any).on("gm:rotateend",onRotateEnd);

    // スタイル再読み込み：ゼロ検知→即リカバリ＋遅延リフレッシュ
    const styleHandler = () => {
      if (!raw.isStyleLoaded()) return;
      gmSourceIdRef.current = resolveGmSourceId();
      applyGmVisualStyle();

      try {
        const gm = gmRef.current as any;
        const exported = gm?.features?.exportGeoJson?.({ idPropertyName: "__gm_id" });
        const count = exported?.features?.length ?? 0;

        if (count === 0 && (lastGoodFcRef.current?.features?.length ?? 0) > 0) {
          gm.features.importGeoJson(lastGoodFcRef.current, {
            idPropertyName: "__gm_id",
            overwrite: true,
          });
          setTimeout(() => refreshWithRetry(), 80);
          return;
        }
      } catch {}

      setTimeout(() => refreshWithRetry(), 120);
    };
    raw.on("styledata", styleHandler);

    // クリーンアップ（削除しない／自然なアンマウント任せ）
    return () => {
      (raw as any).off("gm:create",   onCreate);
      (raw as any).off("gm:editend",  onEditEnd);
      (raw as any).off("gm:remove",   onRemove);
      (raw as any).off("gm:dragend",  onDragEnd);
      (raw as any).off("gm:rotateend",onRotateEnd);
      raw.off("styledata", styleHandler);
      gmRef.current = null;
      initOnceRef.current = false;
    };
  }, [mapRef, initialShapes, translate, refreshWithRetry, syncAfterImport]);

  useEffect(() => {
    const map = mapRef?.getMap();
    if (!map) return;

    // Geoman のメインレイヤーID（fill layer）
    const layers = gmLayerIdsRef.current;
    if (!layers || layers.length === 0) return;

    // 通常は最上位 fill layer が図形クリック検知に使える
    const polyLayerId = layers[0];

    const onPolyClick = (e: any) => {
      const f = e?.features?.[0];
      if (!f) return;

      const gmId =
        f.properties?.__gm_id ||
        f.properties?.client_id ||
        f.id;

      if (!gmId) return;

      // ★ クリックされた図形を選択状態に
      setSelectedAreaId(String(gmId));
    };

    map.on("click", polyLayerId, onPolyClick);

    return () => {
      map.off("click", polyLayerId, onPolyClick);
    };
  }, [mapRef, shapes]);

  // 地図の空白をクリックしたら選択解除
  useEffect(() => {
    const map = mapRef?.getMap();
    if (!map) return;

    const handleMapClick = (e: any) => {
      const features = map.queryRenderedFeatures(e.point);

      // Geoman の layer に当たっているなら解除しない
      const hit = features.some((f: any) => {
        const lid = f?.layer?.id;
        return lid && lid.startsWith("gm_");
      });

      if (!hit) {
        // ★ 選択解除
        setSelectedAreaId(null);
      }
    };

    map.on("click", handleMapClick);

    return () => {
      map.off("click", handleMapClick);
    };
  }, [mapRef]);

  /** ラベル（名前表示用） */
  const labelsGeoJson = useMemo<FeatureCollection>(
    () => ({
      type: "FeatureCollection",
      features: shapes.map((f) => ({
        type: "Feature",
        id: f.id ?? f.properties.gm_id,
        properties: { name: f.properties.name },
        geometry: f.geometry,
      })),
    }),
    [shapes]
  );

  useEffect(() => {
    const raw = mapRef?.getMap() as MaplibreMap | undefined;
    if (!raw) return;
    const srcId = "areas-labels";
    const layerId = "areas-labels-layer";

    const addOrUpdate = () => {
      if (!raw.getSource(srcId)) {
        raw.addSource(srcId, { type: "geojson", data: labelsGeoJson });
        raw.addLayer({
          id: layerId,
          type: "symbol",
          source: srcId,
          layout: { "text-field": ["get", "name"], "text-size": 12 },
          paint: { "text-color": "#111", "text-halo-width": 1, "text-halo-color": "#fff" },
        });
      } else {
        (raw.getSource(srcId) as any)?.setData(labelsGeoJson);
      }
    };

    addOrUpdate();

    return () => {
      try {
        if (raw.getLayer(layerId)) raw.removeLayer(layerId);
        if (raw.getSource(srcId)) raw.removeSource(srcId);
      } catch {}
    };
  }, [mapRef, labelsGeoJson]);

  return <AreaListPanel shapes={shapes} setShapes={setShapes} applyCoordsToFeature={applyCoordsToFeature} removeFeatureById={removeFeatureById} commitNameToFeature={commitNameToFeature} selectedId={selectedAreaId} onSelectArea={setSelectedAreaId} />;
}