/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

"use client";
import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  Collapse,
  Typography,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  IconButton,
  TextField
} from "@mui/material";
import DragIndicatorIcon from '@mui/icons-material/DragIndicator';
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import MenuIcon from "@mui/icons-material/Menu";
import { MAP_Z_INDEX } from "@/components/map/mapZIndex";

import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  DragStartEvent,
  DragEndEvent
} from "@dnd-kit/core";
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { restrictToVerticalAxis, restrictToParentElement } from "@dnd-kit/modifiers";
import { arrayMove } from "@dnd-kit/sortable";
import { useTranslations } from "next-intl";
import { useMap } from "react-map-gl/maplibre";

interface AreaListPanelProps {
  shapes: any[]; // GeoJSON配列
  setShapes: React.Dispatch<React.SetStateAction<any[]>>; // 並び替え用
  applyCoordsToFeature: (gmId: string, coords: [number, number][]) => void;
  removeFeatureById?: (gmId: string) => void;
  commitNameToFeature?: (gmId: string, name: string) => void;
  selectedId?: string | null;
  onSelectArea?: (id: string | null) => void;
}

export default function AreaListPanel({ shapes, setShapes, applyCoordsToFeature, commitNameToFeature, selectedId, onSelectArea }: AreaListPanelProps) {
  const sensors = useSensors(useSensor(PointerSensor));
  const [open, setOpen] = useState(true);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editedName, setEditedName] = useState<string>("");
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const translate = useTranslations("Config");
  const { current: map } = useMap();
  const round6 = (num: number) => Math.round(num * 1e6) / 1e6;

  useEffect(() => {
    if (!selectedId) return;

    const idx = shapes.findIndex(s => s.properties?.gm_id === selectedId);
    if (idx >= 0) {
      setExpandedIndex(idx);
    }
  }, [selectedId, shapes]);

  // gm_id がない場合でも DnD を成立させるための行ID（フォールバック）
  const getRowId = (shape: any, index: number) =>
    String(shape?.properties?.gm_id ?? `__idx_${index}`);

  const handleUpdateVertex = (areaIndex: number, vertexIndex: number, field: "lat" | "lng", value: number) => {
    const shape = shapes[areaIndex];
    const gmId = shape?.properties?.gm_id as string | undefined;
    const next = [...shape.geometry.coordinates[0]] as [number, number][];
    const [lng, lat] = next[vertexIndex];
    next[vertexIndex] = field === "lat" ? [round6(lng), round6(value)] : [round6(value), round6(lat)];

    // UI楽観更新
    setShapes(prev => {
      const updated = [...prev];
      updated[areaIndex] = {
        ...updated[areaIndex],
        geometry: { ...updated[areaIndex].geometry, coordinates: [next] }
      };
      return updated;
    });

    // 地図上へ確実に反映
    if (gmId) applyCoordsToFeature(gmId, next);
  };

  const handleDeleteVertex = (areaIndex: number, vertexIndex: number) => {
    const shape = shapes[areaIndex];
    const gmId = shape?.properties?.gm_id as string | undefined;
    const next = (shape.geometry.coordinates[0] as [number, number][]).filter((_: [number, number], i: number) => i !== vertexIndex);

    // UI楽観更新
    setShapes(prev => {
      const updated = [...prev];
      updated[areaIndex].geometry.coordinates = [next];
      return updated;
    });

    // 地図上へ確実に反映
    if (gmId) applyCoordsToFeature(gmId, next);
  };

  const commitEditName = (index: number) => {
    setShapes(prev => {
      const updated = [...prev];
      const next = editedName.trim(); // 必要なら trim
      if (next.length > 0) {
        updated[index].properties.name = next;
        const gmId = updated[index].properties.gm_id as string | undefined;
        if (gmId && commitNameToFeature) commitNameToFeature(gmId, next);
      }
      return updated;
    });
    setEditingIndex(null);
  };

  return (
    <Box
      sx={{
        position: "absolute",
        top: 10,
        right: 10,
        width: { xs: 250, sm: 340 },
        maxHeight: "80vh",
        overflowY: "auto",
        bgcolor: "background.paper",
        border: "1px solid",
        borderColor: "divider",
        p: 1,
        zIndex: MAP_Z_INDEX.UI_OVERLAY,
        borderRadius: 1,
        boxShadow: 1
      }}
    >
      {/* 親ヘッダー */}
      <Box
        onMouseDown={(e) => {
          e.stopPropagation(); // Reactイベントの伝播を止める
          map?.dragPan?.disable(); // 地図パンを無効化
        }}
        onMouseUp={() => {
          map?.dragPan?.enable(); // 地図パンを再有効化
        }}
        onClick={() => setOpen(!open)}
        sx={{ cursor: "pointer", display: "flex", alignItems: "center", mb: 1, gap: 1 }}
      >
        <MenuIcon fontSize="small" sx={{ color: (t) => (t.palette.mode === "dark" ? "#fff" : "#000") }} />
        <Typography sx={{ ml: 0.75 }} variant="body2">
          {translate("area.listTitle")}
        </Typography>
      </Box>

      <Collapse in={open}>
        {shapes.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            {translate("area.empty")}
          </Typography>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={(event: DragStartEvent) => {
              setDraggingId(event.active.id.toString());
              setExpandedIndex(null);
              map?.dragPan?.disable(); // 地図パンを無効化
            }}
            onDragEnd={(event: DragEndEvent) => {
              setDraggingId(null);
              map?.dragPan?.enable(); // 地図パンを再有効化

              const { active, over } = event;
              if (!over || active.id === over.id) return;

              const findIndexByRowId = (id: string) =>
                shapes.findIndex((s, i) => getRowId(s, i) === id);

              const oldIndex = findIndexByRowId(String(active.id));
              const newIndex = findIndexByRowId(String(over.id));
              if (oldIndex < 0 || newIndex < 0) return;

              setShapes(prev => arrayMove(prev, oldIndex, newIndex));
            }}
            modifiers={[restrictToVerticalAxis, restrictToParentElement]}
          >
            <SortableContext
              items={shapes.map((shape, i) => getRowId(shape, i))}
              strategy={verticalListSortingStrategy}
            >
              {shapes.map((shape, index) => {
                const rowId = getRowId(shape, index);
                return (
                  <SortableAreaRow
                    key={rowId}
                    id={rowId}
                    index={index}
                    shape={shape}
                    isExpanded={expandedIndex === index}
                    selected={shape.properties?.gm_id === selectedId}
                    onSelect={() => onSelectArea?.(shape.properties?.gm_id)}
                    onToggleExpand={() =>
                      setExpandedIndex(prev => (prev === index ? null : index))
                    }
                    isEditing={editingIndex === index}
                    editedName={editedName}
                    onStartEdit={() => {
                      setEditingIndex(index);
                      setEditedName(shape.properties.name ?? "");
                    }}
                    onEditName={(val) => setEditedName(val)}
                    onKeyDownEdit={(e) => {
                      if (e.key === "Enter") commitEditName(index);
                    }}
                    onCancelEdit={() => setEditingIndex(null)}
                    onUpdateVertex={(vertexIndex, field, value) =>
                      handleUpdateVertex(index, vertexIndex, field, value)
                    }
                    onDeleteVertex={(vertexIndex) => handleDeleteVertex(index, vertexIndex)}
                    isDragging={draggingId === rowId}
                    onCommitEdit={() => commitEditName(index)}
                  />
                );
              })}
            </SortableContext>
          </DndContext>
        )}
      </Collapse>
    </Box>
  );
}

interface SortableAreaRowProps {
  id: string;
  index: number;
  shape: any;
  isExpanded: boolean;
  onToggleExpand: () => void;
  isEditing: boolean;
  editedName: string;
  onStartEdit: () => void;
  onEditName: (val: string) => void;
  onKeyDownEdit: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  onCancelEdit: () => void;
  onUpdateVertex: (vertexIndex: number, field: "lat" | "lng", value: number) => void;
  onDeleteVertex: (vertexIndex: number) => void;
  isDragging: boolean;
  onCommitEdit: () => void;
  selected?: boolean;
  onSelect?: () => void;
}

const SortableAreaRow = ({
  id,
  shape,
  isExpanded,
  onToggleExpand,
  isEditing,
  editedName,
  onStartEdit,
  onEditName,
  onKeyDownEdit,
  onUpdateVertex,
  onDeleteVertex,
  isDragging,
  onCommitEdit,
  selected,
  onSelect
}: SortableAreaRowProps) => {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id });
  const translate = useTranslations("Config");

  const coords: [number, number][] = (shape?.geometry?.coordinates?.[0] ?? []) as [number, number][];
  const inputRef = useRef<HTMLInputElement>(null);

  const [tempLat, setTempLat] = useState<{ [key: number]: string }>({});
  const [tempLng, setTempLng] = useState<{ [key: number]: string }>({});

  useEffect(() => {
    if (isEditing && inputRef.current) inputRef.current.focus();
  }, [isEditing]);

  // 確定処理（onBlur / Enter 共用）
  const commitLat = (i: number, original: number) => {
    const raw = tempLat[i] ?? String(original);

    // ====== A. 許容モード：先頭の数値まで反映 ======
    const num = parseFloat(raw);
    if (Number.isFinite(num)) {
      const rounded = Math.round(num * 1e6) / 1e6;
      onUpdateVertex(i, "lat", rounded);
    }

    // ====== B. 厳格モード：1文字でも不正なら反映しない ======
    // const strictNumberRegex = /^-?\d+(\.\d+)?$/;
    // if (strictNumberRegex.test(raw)) {
    //   const num = parseFloat(raw);
    //   const rounded = Math.round(num * 1e6) / 1e6;
    //   onUpdateVertex(i, "lat", rounded);
    // }

    // 入力中キャッシュ消去
    setTempLat(prev => {
      const copy = { ...prev };
      delete copy[i];
      return copy;
    });
  };

  const commitLng = (i: number, original: number) => {
    const raw = tempLng[i] ?? String(original);
    const num = parseFloat(raw);
    if (Number.isFinite(num)) {
      const rounded = Math.round(num * 1e6) / 1e6;
      onUpdateVertex(i, "lng", rounded);
    }
    setTempLng(prev => {
      const copy = { ...prev };
      delete copy[i];
      return copy;
    });
  };

  return (
    <Box
      ref={setNodeRef}
      onClick={() => { if (!isDragging) onSelect?.(); }}
      style={{
        transform: CSS.Transform.toString(transform),
        transition: isDragging ? "none" : transition,
        touchAction: "none",
        userSelect: "none"
      }}
      sx={{
        borderBottom: "1px solid",
        borderColor: "divider",
        py: 0.5,
        bgcolor: selected ? "action.selected" : "transparent",
        // TODO:ここでの "&:hover" は行全体に適用されるため削除/移動する。背景色変更は下の "エリア名ラベル部分" のみで適用する。
        "&:hover": { bgcolor: selected ? "action.selected" : "action.hover" },
      }}
    >
      {/* TODO:エリア展開時にどのエリアを編集しようとしているのか分かるように図形の色を変更する(色は未定) 付随して他箇所の修正も必要*/}
      {/* エリアヘッダー */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          cursor: "pointer"
        }}
        // ドラッグ中は展開トグルしない
        onClick={() => { if (!isDragging) onToggleExpand(); }}
        role="button"
        aria-expanded={isExpanded}
      >
        {/* 左側（矢印 + 名前 or 編集フィールド） */}
        {/* TODO:エリア名ラベル部分に限定したホバー背景を当てる。
        gap: 0.5の後ろに左を追記する "&:hover": { backgroundColor: "#f3f3f3" },*/}
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          {isExpanded ? (
            <KeyboardArrowDownIcon fontSize="small" sx={{ mr: 0.5 }} />
          ) : (
            <KeyboardArrowRightIcon fontSize="small" sx={{ mr: 0.5 }} />
          )}

          {isEditing ? (
            <TextField
              value={editedName}
              onChange={(e) => onEditName(e.target.value)}
              onKeyDown={onKeyDownEdit}
              inputRef={inputRef}
              size="small"
              sx={{ width: "180px", "& input": { padding: 0 } }}
              onClick={(e) => e.stopPropagation()}
              onBlur={onCommitEdit}
            />
          ) : (
            <Typography variant="subtitle2">{shape?.properties?.name ?? ""}</Typography>
          )}
        </Box>

        {/* 右側（編集 / ドラッグハンドル） */}
        <Box sx={{ display: "flex", gap: 0.5 }}>
          <IconButton size="small" onClick={(e) => { e.stopPropagation(); onStartEdit(); }}>
            <EditIcon fontSize="small" />
          </IconButton>
          <IconButton {...attributes} {...listeners} size="small" sx={{ p: 0 }}>
            <DragIndicatorIcon fontSize="small" />
          </IconButton>
        </Box>
      </Box>

      {/* 頂点一覧 */}
      <Collapse in={isExpanded && !isDragging} timeout={0} unmountOnExit>
        <Table size="small" sx={{ mt: 1 }}>
          <TableHead>
            <TableRow>
              <TableCell sx={{ width: "40px" }}>{translate("area.table.id")}</TableCell>
              <TableCell sx={{ width: "45%" }}>{translate("area.table.lat")}</TableCell>
              <TableCell sx={{ width: "45%" }}>{translate("area.table.lng")}</TableCell>
              <TableCell sx={{ width: "36px" }}></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {coords.map((c: [number, number], i: number) => (
              <TableRow key={i}>
                <TableCell sx={{ width: "40px", fontSize: "12px", p: 0.25, textAlign: "center" }}>{i + 1}</TableCell>
                <TableCell sx={{ width: "45%", p: 0.25 }}>
                  <TextField
                    type="text"
                    value={tempLat[i] ?? String(c[1])}
                    onChange={(e) => setTempLat({ ...tempLat, [i]: e.target.value })}
                    onBlur={() => commitLat(i, c[1])}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") commitLat(i, c[1]);
                    }}
                    size="small"
                    fullWidth
                    InputProps={{
                      sx: {
                        fontSize: "12px",
                        fontFamily: "monospace",
                        height: "28px"
                      }
                    }}
                  />
                </TableCell>
                <TableCell sx={{ width: "45%", p: 0.25 }}>
                  <TextField
                    type="text"
                    value={tempLng[i] ?? String(c[0])}
                    onChange={(e) => setTempLng({ ...tempLng, [i]: e.target.value })}
                    onBlur={() => commitLng(i, c[0])}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") commitLng(i, c[0]);
                    }}
                    size="small"
                    fullWidth
                    InputProps={{
                      sx: {
                        fontSize: "12px",
                        fontFamily: "monospace",
                        height: "28px"
                      }
                    }}
                  />
                </TableCell>
                <TableCell sx={{ width: "36px", textAlign: "right", p: 0 }}>
                  <IconButton size="small" color="error" onClick={() => onDeleteVertex(i)}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Collapse>
    </Box>
  );
};