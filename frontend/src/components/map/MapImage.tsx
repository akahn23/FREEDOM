/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

"use client";
import React, { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Source, Layer, useMap } from "react-map-gl/maplibre";
import type maplibregl from "maplibre-gl";

/** === 型定義 === */
export interface ImageResponse {
  name: string;
  corners:
    | [
        [number, number], // TL [lat,lng]
        [number, number], // TR
        [number, number], // BL
        [number, number], // BR
      ]
    | undefined;
  visible?: boolean;
}
type LatLng = [number, number];

type Props = {
  id: string;
  name: string;
  corners: ImageResponse["corners"];
  visible?: boolean;
  editable?: boolean;
  beforeId?: string;
  zIndex?: number;
  options?: Record<string, any>;
  onCornersChange?: (coners: number[][]) => void;
  onDelete?: () => void;

  /** 選択/選択通知（リスト連動用） */
  selected?: boolean;
  onSelect?: (id: string | null) => void;
  src?: string;
};

/** === ユーティリティ === */
const toLngLat = ([lat, lng]: LatLng) => [lng, lat] as [number, number];
function toImageSourceCoordinates(corners?: Props["corners"]) {
  if (!corners || corners.length !== 4) return undefined;
  const [tl, tr, bl, br] = corners;
  // MapLibre image source: [top-left, top-right, bottom-right, bottom-left] (lng,lat)
  return [toLngLat(tl), toLngLat(tr), toLngLat(br), toLngLat(bl)] as any;
}
const sameCorners = (a?: LatLng[], b?: LatLng[]) =>
  !!a && !!b && a.length === 4 && b.length === 4 && a.every((p, i) => p[0] === b[i][0] && p[1] === b[i][1]);

/** === 本体 === */
export default function MapLibreImage({
  id,
  name,
  corners,
  visible = true,
  editable = false,
  beforeId,
  onCornersChange,
  selected = false,
  onSelect,
  src,
}: Props) {
  const [ url, setUrl ] = useState<string | undefined>(src);
  const { current: mapRef } = useMap();
  const map = mapRef?.getMap();

  /** 角のローカル状態 */
  const [localCorners, setLocalCorners] = useState<LatLng[] | undefined>(
    Array.isArray(corners) && corners.length === 4 ? corners : undefined
  );

  // 変形状態（UI制御と<Source>座標凍結に使用）
  const [isTransforming, setIsTransforming] = useState(false);

  const suppressSendRef = useRef(false);

  // 外部 corners 同期（変形中は上書きしない・直前送信と同じは無視）
  const transformingRef = useRef<null | "move" | "scale" | "rotate">(null);
  const lastSentRef = useRef<LatLng[] | undefined>(undefined);
  const frozenCornersRef = useRef<LatLng[] | undefined>(undefined);

  useLayoutEffect(() => {
    if (!Array.isArray(corners) || corners.length !== 4) return;
    // 変形中は props で上書きしない
    if (transformingRef.current) return;
    // 直前送信と同じは無視
    if (lastSentRef.current && sameCorners(lastSentRef.current, corners as any)) return;
    setLocalCorners(prev => (sameCorners(prev as any, corners as any) ? prev : (corners as any)));
    suppressSendRef.current = true;
  }, [corners]);

  /** === 画像と自然サイズを読み取り（アスペクト比用） === */
  const [imgSize, setImgSize] = useState<{ w: number; h: number } | null>(null);
  useEffect(() => {
    const fetchImage = async () => {
      try {
        const res = await fetch(`/api/files/map_images/${name}`);
        if (!res.ok) return;
        setUrl(URL.createObjectURL(await res.blob()));
      } catch (error) {
        console.error(error);
      }
    }
    if (!src) {
      fetchImage();
    }
    if (!url) return;

    let cancelled = false;
    const im = new Image();
    im.onload = () => {
      if (cancelled) return;
      const w = (im as HTMLImageElement).naturalWidth || im.width;
      const h = (im as HTMLImageElement).naturalHeight || im.height;
      if (w && h) {
        setImgSize({ w, h });
      } else {
        // フォールバック（万一 natural サイズが取れない場合）
        setImgSize({ w: 1, h: 1 });
      }
    };
    im.onerror = () => {
      if (!cancelled) setImgSize({ w: 1, h: 1 }); // 読み込み失敗時は 1:1 でフォールバック
    };
    im.src = url;

    return () => {
      if (!src && url) {
        URL.revokeObjectURL(url);
      }
      cancelled = true;
    };
  }, [src, name]);

  // 初期 corners 自動生成（画像アスペクト比で矩形を生成）
  const didInit = useRef(false);
  useEffect(() => {
    if (didInit.current || !map || !editable) return;
    const hasCorners =
      (Array.isArray(corners) && corners.length === 4) ||
      (Array.isArray(localCorners) && localCorners.length === 4);
    if (hasCorners) return;

    // 画像サイズが未取得なら、取得を待つ（onload 後にこの useEffect が再実行される）
    if (!imgSize) return;

    const ratio = imgSize.w / imgSize.h || 1; // w/h
    const center = map.getCenter();
    const cpt = map.project(center);

    // 画面上の初期サイズ（高さ基準）
    const targetHeightPx = 200;               // お好みで調整可能
    const targetWidthPx  = targetHeightPx * ratio;

    const halfW = targetWidthPx  / 2;
    const halfH = targetHeightPx / 2;

    const tl = map.unproject([cpt.x - halfW, cpt.y - halfH] as [number, number]);
    const tr = map.unproject([cpt.x + halfW, cpt.y - halfH] as [number, number]);
    const bl = map.unproject([cpt.x - halfW, cpt.y + halfH] as [number, number]);
    const br = map.unproject([cpt.x + halfW, cpt.y + halfH] as [number, number]);

    setLocalCorners([
      [tl.lat, tl.lng],
      [tr.lat, tr.lng],
      [bl.lat, bl.lng],
      [br.lat, br.lng],
    ]);
    didInit.current = true;
  }, [map, editable, corners, localCorners, imgSize]);

  /** Source の座標（local を優先） + 変形中は凍結 */
  const coordsForSource = useMemo(() => {
    // 変形中は React 経由の Source 座標更新を止める
    const srcCorners =
      isTransforming
        ? // 凍結中は、編集開始時の座標を使う
          frozenCornersRef.current && frozenCornersRef.current.length === 4
          ? frozenCornersRef.current
          : lastSentRef.current && lastSentRef.current.length === 4
          ? lastSentRef.current
          : Array.isArray(corners) && corners.length === 4
          ? corners
          : undefined
        : // 平常時は local を優先
        Array.isArray(localCorners) && localCorners.length === 4
        ? localCorners
        : Array.isArray(corners) && corners.length === 4
        ? corners
        : undefined;
    return toImageSourceCoordinates(srcCorners as any);
  }, [isTransforming, localCorners, corners]);

  // 親への corners 反映（rAF で間引き・変形中は送らない）
  const rafRef = useRef<number | null>(null);
  useEffect(() => {
    if (!editable) return;
    if (!localCorners || localCorners.length !== 4) return;
    if (suppressSendRef.current) {
      suppressSendRef.current = false;
      return;
    }
    if (sameCorners(localCorners, corners as any)) return;
    if (!onCornersChange) return;
    if (transformingRef.current) return;

    if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(() => {
      lastSentRef.current = localCorners;
      onCornersChange(localCorners.map(([lat, lng]) => [lat, lng]));
    });
    return () => {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    };
  }, [editable, localCorners, corners, onCornersChange]);

  const commitCorners = useCallback(() => {
    if (!onCornersChange || !localCorners || localCorners.length !== 4) return;
    onCornersChange(localCorners.map(([lat, lng]) => [lat, lng]));
    lastSentRef.current = localCorners;
  }, [onCornersChange, localCorners]);

  /** ====== 座標変換ヘルパ ====== */
  type Pt = { x: number; y: number };
  const project = (lat: number, lng: number): Pt => {
    const p = map!.project({ lat, lng });
    return { x: p.x, y: p.y };
  };
  const unproject = (p: Pt): LatLng => {
    const ll = map!.unproject([p.x, p.y] as [number, number]);
    return [ll.lat, ll.lng];
  };
  const projectCorners = useCallback((): Pt[] | undefined => {
    if (!map || !localCorners || localCorners.length !== 4) return;
    const [TL, TR, BL, BR] = localCorners;
    return [TL, TR, BL, BR].map(([lat, lng]) => project(lat, lng));
  }, [map, localCorners]);

  /** ====== ヒット用ポリゴン（クリック選択 & 移動ドラッグ） ====== */
  const polygonCoords = useMemo(() => {
    if (!localCorners || localCorners.length !== 4) return undefined;
    const [TL, TR, BL, BR] = localCorners;
    const ring: [number, number][] = [toLngLat(TL), toLngLat(TR), toLngLat(BR), toLngLat(BL), toLngLat(TL)];
    return ring;
  }, [localCorners]);

  const srcId = `img-src-${id}`;
  const layerId = `img-layer-${id}`;
  const hitSrcId = `img-hit-src-${id}`;
  const hitLayerId = `img-hit-layer-${id}`;

  // ==== 枠線＆ハンドル用 Source/Layer ID ====
  const frameSrcId = `img-frame-src-${id}`;
  const frameLayerId = `img-frame-layer-${id}`;

  const handlesSrcId = `img-handles-src-${id}`;
  const cornersLayerId = `img-corner-handles-layer-${id}`;
  const rotHandleLayerId = `img-rot-handle-layer-${id}`;

  /** ====== 履歴（Undo 用） ====== */
  const historyRef = useRef<LatLng[][]>([]);
  const pushHistory = useCallback(() => {
    if (!localCorners) return;
    historyRef.current.push(JSON.parse(JSON.stringify(localCorners)));
    if (historyRef.current.length > 50) historyRef.current.shift();
  }, [localCorners]);

  const imgSourceRef = useRef<maplibregl.ImageSource | null>(null);

  const ensureImageSourceRef = useCallback(() => {
    if (!map) return;
    const s = map.getSource(srcId) as maplibregl.ImageSource | undefined;
    if (s && typeof (s as any).setCoordinates === "function") {
      imgSourceRef.current = s;
    }
  }, [map, srcId]);

  // Source 生成後やスタイル切替時に参照取得
  useEffect(() => {
    if (!map) return;
    ensureImageSourceRef();

    const onStyle = () => ensureImageSourceRef();
    map.on("styledata", onStyle);

    const onSource = (e: any) => {
      // 目的の Source がロードされたら再取得
      if (e?.sourceId === srcId && e?.isSourceLoaded) ensureImageSourceRef();
    };
    map.on("sourcedata", onSource);

    return () => {
      map.off("styledata", onStyle);
      map.off("sourcedata", onSource);
    };
  }, [map, ensureImageSourceRef, srcId]);

  const [beforeReady, setBeforeReady] = useState<boolean>(!beforeId);

  useEffect(() => {
    if (!beforeId) {
      setBeforeReady(true);
      return;
    }
    if (!map) {
      setBeforeReady(false);
      return;
    }

    const check = () => {
      try {
        setBeforeReady(!!map.getLayer(beforeId));
      } catch {
        setBeforeReady(false);
      }
    };

    check();
    map.on("styledata", check);
    map.on("idle", check);
    return () => {
      map.off("styledata", check);
      map.off("idle", check);
    };
  }, [map, beforeId]);

  // ImageSource の座標を “即時” 反映
  const setImageSourceCoords = useCallback((ll: LatLng[]) => {
    const s = imgSourceRef.current;
    if (!s || !ll || ll.length !== 4) return;
    const coords = toImageSourceCoordinates(ll as any)!; // [tl,tr,br,bl] (lng,lat)
    try {
      (s as any).setCoordinates(coords);
    } catch {
      // setCoordinates がまだ使えないタイミングなら無視（次フレームで回復）
    }
  }, []);

  /** ====== 画像の移動（本体ドラッグ） ====== */
  const dragCtxRef = useRef<{ start: Pt; init: Pt[] } | null>(null);
  // rAF 同期用（1 フレーム 1 回に抑制）
  const moveRafRef = useRef<number | null>(null);
  const lastMoveDeltaRef = useRef<{ dx: number; dy: number } | null>(null);

  useEffect(() => {
    if (!map || !polygonCoords) return;

    const onClick = () => onSelect?.(id);

    const onMouseDown = (e: any) => {
      if (!selected || !editable) return;
      if (!localCorners) return;

      e.preventDefault?.();
      try { (map as any).dragPan?.disable(); } catch {}

      pushHistory();
      frozenCornersRef.current = localCorners;
      transformingRef.current = "move";
      setIsTransforming(true);
      setShowEditingUI(false);

      const startPoint = e.point || (e.lngLat ? map.project(e.lngLat) : { x: 0, y: 0 });

      dragCtxRef.current = { start: startPoint, init: projectCorners()! };

      const pump = () => {
        moveRafRef.current = null;
        if (!dragCtxRef.current || !lastMoveDeltaRef.current) return;

        const { dx, dy } = lastMoveDeltaRef.current;
        const movedPx = dragCtxRef.current.init.map((p) => ({
          x: p.x + dx,
          y: p.y + dy,
        }));
        const movedLL = movedPx.map(unproject) as LatLng[];

        setLocalCorners(movedLL);
        setImageSourceCoords(movedLL);
      };

      const onMove = (ev: any) => {
        if (!dragCtxRef.current) return;
        const movePoint = ev.point || (ev.lngLat ? map.project(ev.lngLat) : { x: 0, y: 0 });
        lastMoveDeltaRef.current = {
          dx: movePoint.x - dragCtxRef.current.start.x,
          dy: movePoint.y - dragCtxRef.current.start.y,
        };
        if (moveRafRef.current == null) {
          moveRafRef.current = requestAnimationFrame(pump);
        }
      };

      const onUp = () => {
        dragCtxRef.current = null;
        lastMoveDeltaRef.current = null;
        if (moveRafRef.current != null) cancelAnimationFrame(moveRafRef.current);
        moveRafRef.current = null;

        try { (map as any).dragPan?.enable(); } catch {}
        map.off("mousemove", onMove);
        map.off("mouseup", onUp);
        map.off("mouseout", onUp);
        transformingRef.current = null;
        frozenCornersRef.current = undefined;
        setIsTransforming(false);
        setShowEditingUI(true);

        commitCorners();
      };

      map.on("mousemove", onMove);
      map.on("mouseup", onUp);
      map.on("mouseout", onUp);
    };

    map.on("click", hitLayerId, onClick);
    map.on("mousedown", hitLayerId, onMouseDown);
    return () => {
      map.off("click", hitLayerId, onClick);
      map.off("mousedown", hitLayerId, onMouseDown);
    };
  }, [map, polygonCoords, id, selected, editable, localCorners, onSelect, projectCorners, pushHistory, commitCorners, setImageSourceCoords ]);

  /** ====== 等比スケール（四隅汎用版）– 反転対応（負スケール）＋退化防止 ====== */
  const updateByCornerDrag = useCallback(
    (corner: "TL" | "TR" | "BL" | "BR", newLng: number, newLat: number) => {
      if (!map) return;

      // 緯度経度の安全化ヘルパ
      const clampLL = ([lat, lng]: [number, number]): [number, number] => {
        const MAX_LAT = 85.05112878;
        const L = Math.max(-MAX_LAT, Math.min(MAX_LAT, lat));
        let E = ((lng + 540) % 360) - 180; // wrap to [-180,180)
        return [L, E];
      };
      const isFiniteLL = ([lat, lng]: [number, number]) =>
        Number.isFinite(lat) && Number.isFinite(lng);

      setLocalCorners(prev => {
        const base: LatLng[] | undefined =
          prev && prev.length === 4 ? prev : (Array.isArray(corners) && corners.length === 4 ? corners : undefined);
        if (!base || base.length !== 4) return prev;

        const [TL, TR, BL, BR] = base;
        const TLpx = project(TL[0], TL[1]);
        const TRpx = project(TR[0], TR[1]);
        const BLpx = project(BL[0], BL[1]);
        const BRpx = project(BR[0], BR[1]);
        const newP = project(newLat, newLng);

        let A: Pt, v1: Pt, v2: Pt; // アンカーと基底
        // 角ごとにアンカー（対角）と基底ベクトル(a,b)をセット
        if (corner === "BL") {
          A = TRpx; v1 = { x: TLpx.x - TRpx.x, y: TLpx.y - TRpx.y }; v2 = { x: BRpx.x - TRpx.x, y: BRpx.y - TRpx.y };
        } else if (corner === "TR") {
          A = BLpx; v1 = { x: TLpx.x - BLpx.x, y: TLpx.y - BLpx.y }; v2 = { x: BRpx.x - BLpx.x, y: BRpx.y - BLpx.y };
        } else if (corner === "TL") {
          A = BRpx; v1 = { x: TRpx.x - BRpx.x, y: TRpx.y - BRpx.y }; v2 = { x: BLpx.x - BRpx.x, y: BLpx.y - BRpx.y };
        } else { // "BR"
          A = TLpx; v1 = { x: TRpx.x - TLpx.x, y: TRpx.y - TLpx.y }; v2 = { x: BLpx.x - TLpx.x, y: BLpx.y - TLpx.y };
        }

        const d  = { x: v1.x + v2.x, y: v1.y + v2.y }; // 対角方向
        const vv = { x: newP.x - A.x, y: newP.y - A.y };

        const denom = d.x * d.x + d.y * d.y;
        if (denom < 1e-9) return prev; // 数値安定性

        // 等比スケール係数 t（負も許可 = 反転可）
        let t = (vv.x * d.x + vv.y * d.y) / denom;

        // 退化防止：|t| の最小値を確保、かつ上限も設定
        const MIN_ABS = 0.10;
        const MAX_ABS = 10.0;
        if (Math.abs(t) < MIN_ABS) t = t >= 0 ? MIN_ABS : -MIN_ABS;
        t = Math.sign(t) * Math.min(Math.abs(t), MAX_ABS);

        // 新しい 3 点（A 固定・等比 t 倍）
        const P1 = { x: A.x + t * v1.x, y: A.y + t * v1.y };       // A + t v1
        const P2 = { x: A.x + t * v2.x, y: A.y + t * v2.y };       // A + t v2
        const PD = { x: A.x + t * (v1.x + v2.x), y: A.y + t * (v1.y + v2.y) }; // A + t (v1+v2)

        // 角ごとに新しい四隅を組み立て
        let TLp = TLpx, TRp = TRpx, BLp = BLpx, BRp = BRpx;
        if (corner === "BL") { TLp = P1; BRp = P2; BLp = PD; TRp = A; }
        else if (corner === "TR") { TLp = P1; BRp = P2; TRp = PD; BLp = A; }
        else if (corner === "TL") { TRp = P1; BLp = P2; TLp = PD; BRp = A; }
        else /* BR */ { TRp = P1; BLp = P2; BRp = PD; TLp = A; }

        const TLll = clampLL(unproject(TLp));
        const TRll = clampLL(unproject(TRp));
        const BLll = clampLL(unproject(BLp));
        const BRll = clampLL(unproject(BRp));

        if (![TLll, TRll, BLll, BRll].every(isFiniteLL)) return prev;

        const newLL: LatLng[] = [
          [TLll[0], TLll[1]],
          [TRll[0], TRll[1]],
          [BLll[0], BLll[1]],
          [BRll[0], BRll[1]],
        ];

        setImageSourceCoords(newLL);
        return newLL;
      });
    },
    [map, corners, setImageSourceCoords]
  );

  /** ====== 回転（WebGLレイヤ用に微調整・スナップ付き） ====== */
  const rotRafRef = useRef<number | null>(null);
  const latestPointerRef = useRef<Pt | null>(null);
  const rotateDragCtx = useRef<{ center: Pt; startMouse: Pt; init: Pt[] } | null>(null);
  const beginRotate = useCallback(
    (startLng: number, startLat: number) => {
      if (!map || !localCorners) return;
      const ps = projectCorners()!;
      const center = {
        x: (ps[0].x + ps[1].x + ps[2].x + ps[3].x) / 4,
        y: (ps[0].y + ps[1].y + ps[2].y + ps[3].y) / 4,
      };
      try { (map as any).dragPan?.disable(); } catch {}
      rotateDragCtx.current = {
        center,
        startMouse: map.project({ lat: startLat, lng: startLng }),
        init: ps,
      };
      frozenCornersRef.current = localCorners;
      transformingRef.current = "rotate";
      setIsTransforming(true);
      pushHistory();
      setShowEditingUI(false);
    },
    [map, localCorners, projectCorners, pushHistory]
  );

  // 角度スナップ（0/90/180/270 ±1°）
  const snapAngleDeg = (deg: number) => {
    const targets = [0, 90, 180, 270, 360];
    const SNAP = 1.0;
    let nearest = targets[0];
    for (const t of targets) if (Math.abs(t - deg) < Math.abs(nearest - deg)) nearest = t;
    return Math.abs(nearest - deg) <= SNAP ? nearest % 360 : deg;
  };

  const onRotateDrag = useCallback(
    (lng: number, lat: number) => {
      if (!map || !rotateDragCtx.current) return;
      latestPointerRef.current = map.project({ lat, lng });
      if (rotRafRef.current != null) return;

      rotRafRef.current = requestAnimationFrame(() => {
        rotRafRef.current = null;
        const ctx = rotateDragCtx.current!;
        const now = latestPointerRef.current!;
        const a0 = Math.atan2(ctx.startMouse.y - ctx.center.y, ctx.startMouse.x - ctx.center.x);
        const a1 = Math.atan2(now.y - ctx.center.y, now.x - ctx.center.x);
        let d = a1 - a0;

        // 角度スナップ
        const deg = ((d * 180) / Math.PI + 360) % 360;
        const degSnapped = snapAngleDeg(deg);
        const dFinal = (degSnapped * Math.PI) / 180;

        const cos = Math.cos(dFinal), sin = Math.sin(dFinal);
        const rot = ctx.init.map((p) => {
          const rx = p.x - ctx.center.x;
          const ry = p.y - ctx.center.y;
          return { x: ctx.center.x + rx * cos - ry * sin, y: ctx.center.y + rx * sin + ry * cos };
        });
        const movedLL = rot.map(unproject) as LatLng[];

        setLocalCorners(movedLL);
        setImageSourceCoords(movedLL);
      });
    },
    [map, setImageSourceCoords]
  );

  const endRotate = useCallback(() => {
    // rAF後片付け
    if (rotRafRef.current != null) {
      cancelAnimationFrame(rotRafRef.current);
      rotRafRef.current = null;
    }
    latestPointerRef.current = null;

    // 水平/垂直の丸め（ピタッと合わせる）
    const EPS = 0.75; // px 許容
    const ps = projectCorners();
    if (ps && ps.length === 4) {
      const dyTop = ps[0].y - ps[1].y;   // TL-TR
      const dyBottom = ps[2].y - ps[3].y; // BL-BR
      const dxLeft = ps[0].x - ps[2].x;  // TL-BL
      const dxRight = ps[1].x - ps[3].x; // TR-BR
      let changed = false;

      // 水平揃え
      if (Math.abs(dyTop) < EPS && Math.abs(dyBottom) < EPS) {
        const yTop = (ps[0].y + ps[1].y) / 2;
        const yBottom = (ps[2].y + ps[3].y) / 2;
        ps[0].y = ps[1].y = yTop;
        ps[2].y = ps[3].y = yBottom;
        changed = true;
      }
      // 垂直揃え
      if (Math.abs(dxLeft) < EPS && Math.abs(dxRight) < EPS) {
        const xLeft = (ps[0].x + ps[2].x) / 2;
        const xRight = (ps[1].x + ps[3].x) / 2;
        ps[0].x = ps[2].x = xLeft;
        ps[1].x = ps[3].x = xRight;
        changed = true;
      }

      if (changed) {
        const ll = ps.map(p => unproject(p));
        const newLL: LatLng[] = [
          [ll[0][0], ll[0][1]],
          [ll[1][0], ll[1][1]],
          [ll[2][0], ll[2][1]],
          [ll[3][0], ll[3][1]],
        ];
        setLocalCorners(newLL);
        setImageSourceCoords(newLL);
      }
    }

    // 地図パンを再有効化
    try { (map as any).dragPan?.enable(); } catch {}
    transformingRef.current = null;
    frozenCornersRef.current = undefined;
    setIsTransforming(false);
    setShowEditingUI(true);
  }, [map, projectCorners, setImageSourceCoords]);

  /** ====== 回転ハンドルの座標（上辺中央から外側へ 40px） ====== */
  const rotateHandleLngLat = useMemo(() => {
    if (!map || !localCorners) return undefined;
    const [TL, TR, BL, BR] = localCorners;
    const pTL = project(TL[0], TL[1]);
    const pTR = project(TR[0], TR[1]);
    const pBL = project(BL[0], BL[1]);
    const pBR = project(BR[0], BR[1]);

    const mid = { x: (pTL.x + pTR.x) / 2, y: (pTL.y + pTR.y) / 2 }; // 上辺中点
    const center = { x: (pTL.x + pTR.x + pBL.x + pBR.x) / 4, y: (pTL.y + pTR.y + pBL.y + pBR.y) / 4 };
    const ex = { x: pTR.x - pTL.x, y: pTR.y - pTL.y };
    const len = Math.hypot(ex.x, ex.y) || 1;
    const nx = -ex.y / len, ny = ex.x / len; // 上辺の法線
    const d = 40; // オフセット px
    const cand1 = { x: mid.x + nx * d, y: mid.y + ny * d };
    const cand2 = { x: mid.x - nx * d, y: mid.y - ny * d };
    const dist1 = (cand1.x - center.x) ** 2 + (cand1.y - center.y) ** 2;
    const dist2 = (cand2.x - center.x) ** 2 + (cand2.y - center.y) ** 2;
    const pos = dist1 > dist2 ? cand1 : cand2; // より外側を採用
    const ll = unproject(pos);
    return { lat: ll[0], lng: ll[1] };
  }, [map, localCorners]);

  /** ====== 四隅＋回転ハンドルの GeoJSON = 同一WebGLで描画 ====== */
  const handleGeoJSON = useMemo(() => {
    if (!localCorners || !rotateHandleLngLat) return null;
    const [TL, TR, BL, BR] = localCorners;
    const features: any[] = [
      { type: "Feature", geometry: { type: "Point", coordinates: [TL[1], TL[0]] }, properties: { id: "TL", kind: "corner" } },
      { type: "Feature", geometry: { type: "Point", coordinates: [TR[1], TR[0]] }, properties: { id: "TR", kind: "corner" } },
      { type: "Feature", geometry: { type: "Point", coordinates: [BL[1], BL[0]] }, properties: { id: "BL", kind: "corner" } },
      { type: "Feature", geometry: { type: "Point", coordinates: [BR[1], BR[0]] }, properties: { id: "BR", kind: "corner" } },
      { type: "Feature", geometry: { type: "Point", coordinates: [rotateHandleLngLat.lng, rotateHandleLngLat.lat] }, properties: { id: "ROT", kind: "rotate" } },
    ];
    return { type: "FeatureCollection", features };
  }, [localCorners, rotateHandleLngLat]);

  /** ====== 枠線 LineString（四隅を結ぶ） ====== */
  const frameLineGeoJSON = useMemo(() => {
    if (!localCorners) return null;
    const coords = [
      [localCorners[0][1], localCorners[0][0]], // TL
      [localCorners[1][1], localCorners[1][0]], // TR
      [localCorners[3][1], localCorners[3][0]], // BR
      [localCorners[2][1], localCorners[2][0]], // BL
      [localCorners[0][1], localCorners[0][0]], // close
    ];
    return {
      type: "Feature",
      geometry: { type: "LineString", coordinates: coords },
      properties: { id },
    } as const;
  }, [localCorners, id]);

  const [showEditingUI, setShowEditingUI] = useState(true);

  /** ====== 地図の空白クリックで選択解除 ====== */
  useEffect(() => {
    if (!map) return;

    const onBackgroundClick = (e: any) => {
      if (transformingRef.current) return;
      const features = map.queryRenderedFeatures(e.point);
      const clickedOnAny = Array.isArray(features) && features.some((f: any) => {
        const lid = f?.layer?.id;
        return typeof lid === "string" && (lid.startsWith("img-hit-layer-") || lid.startsWith("img-corner-handles-layer-") || lid.startsWith("img-rot-handle-layer-") || lid.startsWith("img-frame-layer-"));
      });
      if (clickedOnAny) return;
      onSelect?.(null);
    };

    map.on("click", onBackgroundClick);
    return () => { map.off("click", onBackgroundClick); };
  }, [map, onSelect]);

  /** ====== スケール用 rAF （四隅ドラッグのイベントレートを1フレーム1回に抑制） ====== */
  const scaleRafRef = useRef<number | null>(null);
  const latestScaleRef = useRef<{
    cid: "TL" | "TR" | "BL" | "BR";
    lng: number;
    lat: number;
  } | null>(null);

  const flushScale = useCallback(() => {
    scaleRafRef.current = null;
    const s = latestScaleRef.current;
    if (!s) return;
    updateByCornerDrag(s.cid, s.lng, s.lat);
  }, [updateByCornerDrag]);

  /** ====== ハンドルのドラッグ（Layer イベント） ====== */
  useEffect(() => {
    if (!map || !editable || !selected) return;

    // ==== 四隅スケール ====
    const onCornerDown = (e: any) => {
      const feat = e.features?.[0];
      if (!feat) return;
      if (feat.properties?.kind !== "corner") return;
      const cid = feat.properties?.id as "TL" | "TR" | "BL" | "BR";
      if (!cid) return;

      e.preventDefault?.();
      try { (map as any).dragPan?.disable(); } catch {}

      frozenCornersRef.current = localCorners ?? undefined;
      transformingRef.current = "scale";
      setIsTransforming(true);
      pushHistory();
      setShowEditingUI(false);
      const onMove = (ev: any) => {
        const { lng, lat } = ev.lngLat;
        latestScaleRef.current = { cid, lng, lat };
        if (scaleRafRef.current == null) {
          scaleRafRef.current = requestAnimationFrame(flushScale);
        }
      };
      const onUp = (ev: any) => {
        const { lng, lat } = ev.lngLat;
        // 最終反映を一回だけ保証
        latestScaleRef.current = { cid, lng, lat };
        if (scaleRafRef.current != null) cancelAnimationFrame(scaleRafRef.current);
        flushScale();

        transformingRef.current = null;
  frozenCornersRef.current = undefined;
        setIsTransforming(false);
        try { (map as any).dragPan?.enable(); } catch {}
        map.off("mousemove", onMove);
        map.off("mouseup", onUp);
        map.off("mouseout", onUp);
        setShowEditingUI(true);
        commitCorners();
      };

      map.on("mousemove", onMove);
      map.on("mouseup", onUp);
      map.on("mouseout", onUp);
    };

    // ==== 回転 ====
    const onRotateDown = (e: any) => {
      const feat = e.features?.[0];
      if (!feat || feat.properties?.kind !== "rotate") return;
      const { lng, lat } = e.lngLat;
      beginRotate(lng, lat);
    };
    const onRotateMove = (e: any) => {
      if (transformingRef.current !== "rotate") return;
      const { lng, lat } = e.lngLat;
      onRotateDrag(lng, lat);
    };
    const onRotateUp = (e: any) => {
      if (transformingRef.current !== "rotate") return;
      const { lng, lat } = e.lngLat;
      onRotateDrag(lng, lat);
      endRotate();
      commitCorners();
    };

    map.on("mousedown", cornersLayerId, onCornerDown);
    map.on("mousedown", rotHandleLayerId, onRotateDown);
    map.on("mousemove", onRotateMove);
    map.on("mouseup", onRotateUp);
    map.on("mouseout", onRotateUp);

    return () => {
      map.off("mousedown", cornersLayerId, onCornerDown);
      map.off("mousedown", rotHandleLayerId, onRotateDown);
      map.off("mousemove", onRotateMove);
      map.off("mouseup", onRotateUp);
      map.off("mouseout", onRotateUp);
    };
  }, [map, editable, selected, beginRotate, onRotateDrag, endRotate, commitCorners, pushHistory, flushScale]);

  if (!name) return null;

  return (
    <>
      {/* 画像ソース */}
      {url && coordsForSource && (
        <Source id={srcId} type="image" url={url} coordinates={coordsForSource} />
      )}
      {/* ラスターレイヤ */}
      {coordsForSource && (!beforeId || beforeReady) && (
        <Layer
          id={layerId}
          type="raster"
          source={srcId}
          layout={{ visibility: visible ? "visible" : "none" }}
          paint={{ "raster-opacity": 1 }}
          beforeId={beforeId}
        />
      )}

      {/* ヒット用ポリゴン（選択強調 & クリックターゲット） */}
      {localCorners && visible && (
        <Source
          id={hitSrcId}
          type="geojson"
          data={{
            type: "Feature",
            geometry: {
              type: "Polygon",
              coordinates: [[
                toLngLat(localCorners[0]),
                toLngLat(localCorners[1]),
                toLngLat(localCorners[3]),
                toLngLat(localCorners[2]),
                toLngLat(localCorners[0]),
              ]],
            },
            properties: { id },
          }}
        />
      )}
      {localCorners && visible && (
        <Layer
          id={hitLayerId}
          type="fill"
          source={hitSrcId}
          paint={{
            "fill-color": "#000000",
            "fill-opacity": 0.001,
            "fill-outline-color": "rgba(0, 0, 0, 0)",
          }}
        />
      )}

      {/* 枠線（PowerPoint 風の外枠） */}
      {editable && selected && showEditingUI && frameLineGeoJSON && (
        <>
          <Source id={frameSrcId} type="geojson" data={frameLineGeoJSON as any} />
          <Layer
            id={frameLayerId}
            type="line"
            source={frameSrcId}
            layout={{
              visibility: visible ? "visible" : "none",
              "line-cap": "round",
              "line-join": "round",
            }}
            paint={{
              "line-color": "#000000",
              "line-width": 0.5,
              "line-opacity": 1,
              // "line-dasharray": [2, 2], // 破線にしたい場合
            }}
          />
        </>
      )}

      {/* === ハンドル群（WebGLレイヤ / 選択時のみ表示）=== */}
      {editable && selected && showEditingUI && handleGeoJSON && (
        <>
          <Source id={handlesSrcId} type="geojson" data={handleGeoJSON as any} />
          {/* 四隅ハンドル（白縁・青） */}
          <Layer
            id={cornersLayerId}
            type="circle"
            source={handlesSrcId}
            filter={["==", ["get", "kind"], "corner"]}
            paint={{
              "circle-radius": 6,
              "circle-color": "#0078D4",
              "circle-stroke-color": "#ffffff",
              "circle-stroke-width": 2,
            }}
          />
          {/* 回転ハンドル（⟳ テキスト） */}
          <Layer
            id={rotHandleLayerId}
            type="symbol"
            source={handlesSrcId}
            filter={["==", ["get", "kind"], "rotate"]}
            layout={{
              "text-field": "⟳",
              "text-size": 18,
              "text-font": ["Noto Sans Regular", "Arial Unicode MS"],
              "text-allow-overlap": true,
              "text-ignore-placement": true,
              "text-offset": [0, 0],
              "text-anchor": "center",
            }}
            paint={{
              "text-color": "#000000",
              "text-halo-color": "#ffffff",
              "text-halo-width": 1.5,
            }}
          />
        </>
      )}
    </>
  );
}
