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
import type { IntersectionAreaGeoJSON } from "./IntersectionDraw";

interface IntersectionListPanelProps {
  title: string; // 一覧タイトル
  mode: "entry" | "reserve";
  shapes: IntersectionAreaGeoJSON[];
  setShapes: React.Dispatch<React.SetStateAction<IntersectionAreaGeoJSON[]>>;
  applyCoordsToFeature: (gmId: string, coords: [number, number][]) => void;
  removeFeatureById?: (gmId: string) => void;
  commitNameToFeature?: (
    gmId: string,
    name: string,
    mode: "entry" | "reserve"
  ) => void;
  commitPriorityToFeature?: (gmId: string, priority?: number) => void;
  showPriority?: boolean;
  sx?: object;
  selectedId?: string | null; onSelect?: (id: string | null) => void;
}

export default function IntersectionListPanel({ title, mode, shapes, setShapes, applyCoordsToFeature, removeFeatureById, commitNameToFeature, commitPriorityToFeature, showPriority = false, sx, selectedId, onSelect }: IntersectionListPanelProps) {
  const sensors = useSensors(useSensor(PointerSensor));
  const [open, setOpen] = useState(true);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editedName, setEditedName] = useState<string>("");
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const translate = useTranslations("Config");
  const { current: map } = useMap();
  const panelRef = useRef<HTMLDivElement | null>(null);

  // gm_id がない場合でも DnD を成立させるフォールバックID
  const getRowId = (shape: any, index: number) =>
    String(shape?.properties?.gm_id ?? `__idx_${index}`);

  const handleUpdateVertex = (areaIndex: number, vertexIndex: number, field: "lat" | "lng", value: number) => {
    const shape = shapes[areaIndex];
    const gmId = shape?.properties?.gm_id as string | undefined;
    const next = [...(shape.geometry.coordinates[0] as [number, number][])];
    const [lng, lat] = next[vertexIndex];
    next[vertexIndex] = field === "lat" ? [lng, value] : [value, lat];

    // UI楽観更新
    setShapes(prev => {
      const updated = [...prev];
      updated[areaIndex] = {
        ...updated[areaIndex],
        geometry: { ...updated[areaIndex].geometry, coordinates: [next] }
      } as IntersectionAreaGeoJSON;
      return updated;
    });

    // 地図上へ確実に反映
    if (gmId) applyCoordsToFeature(gmId, next);
  };

  const handleDeleteVertex = (areaIndex: number, vertexIndex: number) => {
    const shape = shapes[areaIndex];
    const gmId = shape?.properties?.gm_id as string | undefined;
    const next = (shape.geometry.coordinates[0] as [number, number][]).filter((_, i) => i !== vertexIndex);

    // UI楽観更新
    setShapes(prev => {
      const updated = [...prev];
      updated[areaIndex] = {
        ...updated[areaIndex],
        geometry: { ...updated[areaIndex].geometry, coordinates: [next] },
      } as IntersectionAreaGeoJSON;
      return updated;
    });

    // 地図上へ確実に反映
    if (gmId) applyCoordsToFeature(gmId, next);
  };

  // 名前確定
  const commitEditName = (index: number) => {
    const gmId = shapes[index]?.properties?.gm_id as string | undefined;
    const next = (editedName ?? "").trim();
    if (gmId && commitNameToFeature) {
      commitNameToFeature(gmId, next, mode);
    }
    setEditingIndex(null);
  };

  // パネル内操作が地図パンに伝わらないようにする
  useEffect(() => {
    if (!panelRef.current) return;
    const el = panelRef.current;
    const stop = (e: Event) => e.stopPropagation();

    el.addEventListener("wheel", stop, { passive: true });
    el.addEventListener("mousedown", stop);
    el.addEventListener("touchstart", stop);
    return () => {
      el.removeEventListener("wheel", stop);
      el.removeEventListener("mousedown", stop);
      el.removeEventListener("touchstart", stop);
    };
  }, []);

  return (
    <Box
      ref={panelRef}
      sx={{
        position: "relative",
        ...sx,
        width: "100%",
        bgcolor: "background.paper",
        border: "1px solid",
        borderColor: "divider",
        p: 1,
        borderRadius: 1,
        boxShadow: 1,
        mb: 1,
        display: "flex",
        flexDirection: "column",
        maxHeight: "50%",
        pointerEvents: "auto",
      }}
    >
      {/* ヘッダー */}
      <Box
        onMouseDown={(e) => {
          e.stopPropagation(); // Reactイベントの伝播を止める
          map?.dragPan?.disable(); //  地図パンを無効化
        }}
        onMouseUp={() => {
          map?.dragPan?.enable(); //  地図パンを再有効化
        }}
        onClick={() => setOpen(!open)}
        sx={{ cursor: "pointer", display: "flex", alignItems: "center", mb: 1, gap: 1 }}
      >
        <MenuIcon fontSize="small" sx={{ color: (t) => (t.palette.mode === "dark" ? "#fff" : "#000") }} />
        <Typography sx={{ ml: 0.75 }} variant="body2">
          {title} {/*  propsで受け取ったタイトル */}
        </Typography>
      </Box>

      <Box sx={{ overflowY: "auto", height: "100%", flexGrow: 1, pr: 0.5 }}>
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
                setDraggingId(String(event.active.id));
                setExpandedIndex(null);
                map?.dragPan?.disable(); //  地図のパンを無効化
              }}
              onDragEnd={(event: DragEndEvent) => {
                setDraggingId(null);
                map?.dragPan?.enable(); //  地図のパンを再有効化

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
                  const gmId = shape?.properties?.gm_id as (string | undefined);
                  const selected = !!gmId && selectedId === gmId;
                  return (
                    <SortableAreaRow
                      key={rowId}
                      id={rowId}
                      index={index}
                      shape={shape}
                      selected={selected}
                      onSelectRow={() => onSelect?.(gmId ?? null)}
                      isExpanded={expandedIndex === index}
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
                      onDeleteVertex={(vertexIndex) =>
                        handleDeleteVertex(index, vertexIndex)
                      }
                      isDragging={draggingId === rowId}
                      onCommitEdit={() => commitEditName(index)}
                      showPriority={showPriority}
                      onDeleteArea={() => {
                        const gmId = shape?.properties?.gm_id;
                        if (gmId && removeFeatureById) removeFeatureById(gmId);
                        if (gmId && selectedId === gmId) {
                          onSelect?.(null);
                        }
                        setShapes(prev => prev.filter((_, i) => i !== index));
                      }}
                      commitPriorityToFeature={commitPriorityToFeature}
                    />
                  );
                })}
              </SortableContext>
            </DndContext>
          )}
        </Collapse>
      </Box>
    </Box>
  );
}

interface SortableAreaRowProps {
  id: string;
  index: number;
  shape: IntersectionAreaGeoJSON;
  selected: boolean; onSelectRow: () => void;
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
  showPriority?: boolean;
  onDeleteArea: () => void;
  commitPriorityToFeature?: (gmId: string, priority?: number) => void;
}

const SortableAreaRow = ({
  id,
  shape,
  selected,
  onSelectRow,
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
  showPriority,
  commitPriorityToFeature,
}: SortableAreaRowProps) => {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id });
  const translate = useTranslations("Config");
  const coords = (shape?.geometry?.coordinates?.[0] ?? []) as [number, number][];
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) inputRef.current.focus();
  }, [isEditing]);

  const toNumWithFallback = (prev: number, v: string) => {
    const n = parseFloat(v);
    return Number.isFinite(n) ? n : prev;
  };

  return (
    <Box
      ref={setNodeRef}
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
        // TODO:ここでの "&:hover" は行全体に適用されるため削除/移動する。背景色変更は下の "エリア名ラベル部分" のみで適用する。
        "&:hover": { backgroundColor: "#f3f3f3" }, // ホバー効果 ← この行は削除する
        bgcolor: selected ? "action.selected" : "transparent"
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
        // ★ クリックで選択 → 展開トグル（ドラッグ中は無効)
        onClick={() => { if (!isDragging) { onSelectRow(); onToggleExpand(); } }}
        role="button"
        aria-expanded={isExpanded}
        aria-selected={selected}
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
              sx={{ width: { xs: "110px", sm: "160px" }, "& input": { padding: 0 } }}
              onClick={(e) => e.stopPropagation()}
              onFocus={() => onSelectRow()}
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
            {coords.map((c, i) => (
              <TableRow key={i}>
                <TableCell sx={{ width: "40px", fontSize: "12px", p: 0.25, textAlign: "center" }}>{i + 1}</TableCell>
                <TableCell sx={{ width: "45%", p: 0.25 }}>
                  <TextField
                    type="number"
                    value={c[1]}
                    onChange={(e) => onUpdateVertex(i, "lat", toNumWithFallback(c[1], e.target.value))}
                    size="small"
                    fullWidth
                    InputProps={{
                      sx: {
                        fontSize: "12px",
                        fontFamily: "monospace",
                        height: "28px",
                        // '& input[type=number]': {
                        //   MozAppearance: 'textfield', // Firefoxの場合必要
                        // },
                        '& input[type=number]::-webkit-outer-spin-button': {
                          WebkitAppearance: 'none',
                          margin: 0,
                        },
                        '& input[type=number]::-webkit-inner-spin-button': {
                          WebkitAppearance: 'none',
                          margin: 0,
                        },
                      }
                    }}
                  />
                </TableCell>
                <TableCell sx={{ width: "45%", p: 0.25 }}>
                  <TextField
                    type="number"
                    value={c[0]}
                    onChange={(e) => onUpdateVertex(i, "lng", toNumWithFallback(c[0], e.target.value))}
                    size="small"
                    fullWidth
                    InputProps={{
                      sx: {
                        fontSize: "12px",
                        fontFamily: "monospace",
                        height: "28px",
                        // '& input[type=number]': {
                        //   MozAppearance: 'textfield', // Firefoxの場合必要
                        // },
                        '& input[type=number]::-webkit-outer-spin-button': {
                          WebkitAppearance: 'none',
                          margin: 0,
                        },
                        '& input[type=number]::-webkit-inner-spin-button': {
                          WebkitAppearance: 'none',
                          margin: 0,
                        },
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

        {/*  優先度入力欄 */}
        {showPriority && (
          <Box sx={{ mt: 1, display: "flex", justifyContent: "flex-end" }}>
            <TextField
              type="number"
              size="small"
              label={translate("intersection.priority")} //  ラベルを中に表示
              variant="outlined"
              value={shape.properties.priority ?? ""}
              onChange={(e) => {
                const val = e.target.value === "" ? undefined : parseInt(e.target.value, 10);
                const gmId = shape?.properties?.gm_id;
                if (gmId && commitPriorityToFeature) {
                  commitPriorityToFeature(gmId, val);
                }
              }}
              error={shape.properties.priority === undefined || Number.isNaN(shape.properties.priority)}
              helperText={shape.properties.priority === undefined ? "必須項目です" : ""}
              sx={{
                width: "120px",
                ml: "auto",
                mr: "36px", //  ゴミ箱アイコン分調整
                textAlign: "right",
              }}
              InputProps={{
                sx: {
                  fontSize: "12px",
                  fontFamily: "monospace",
                  height: "36px",
                  '& input[type=number]::-webkit-outer-spin-button': {
                    WebkitAppearance: 'none',
                    margin: 0,
                  },
                  '& input[type=number]::-webkit-inner-spin-button': {
                    WebkitAppearance: 'none',
                    margin: 0,
                  },
                  textAlign: "right", //  入力文字も右寄せ
                }
              }}
            />
          </Box>
        )}
      </Collapse>
    </Box>
  );
};