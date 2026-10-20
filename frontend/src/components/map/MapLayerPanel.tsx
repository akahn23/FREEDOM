/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

"use client";
import * as React from "react";
import { useTranslations } from "next-intl";
import {
  Box, Paper, IconButton, List, ListItem, ListItemButton,
  ListItemText, Button, Divider, Collapse
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import VisibilityIcon from "@mui/icons-material/Visibility";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import DragIndicatorIcon from "@mui/icons-material/DragIndicator";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";

import {
  DndContext, DragEndEvent, PointerSensor, useSensor, useSensors
} from "@dnd-kit/core";
import {
  SortableContext, verticalListSortingStrategy, useSortable
} from "@dnd-kit/sortable";
import { restrictToVerticalAxis, restrictToFirstScrollableAncestor } from "@dnd-kit/modifiers";
import { CSS } from "@dnd-kit/utilities";
import { MAP_Z_INDEX } from "@/components/map/mapZIndex";

export type LayerItem = { id: string; name: string; visible: boolean };

type Props = {
  items: LayerItem[];
  onReorder: (from: number, to: number) => void;
  onToggleVisible: (id: string, next: boolean) => void;
  onAdd: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onDelete: (id: string) => void;
  selectedId?: string | null;
  onSelect?: (id: string | null) => void;
  offset?: { top: number; right: number };
  width?: number | Record<string, number>;
  maxBodyHeight?: number;
  defaultOpen?: boolean;
  zIndex?: number;
};

function Row({
  item, selected, onSelect, onToggleVisible,
}: {
  item: LayerItem;
  selected: boolean;
  onSelect?: (id: string) => void;
  onToggleVisible: (id: string, next: boolean) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: item.id });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.6 : 1,
  };

  return (
    <ListItem ref={setNodeRef} style={style} disablePadding sx={{ userSelect: "none" }}>
      <ListItemButton
        selected={selected}
        onClick={() => onSelect?.(item.id)}
        sx={{
          pr: 1,
          "&:hover": { backgroundColor: (t) => t.palette.action.hover },
          display: "flex",
          alignItems: "center",
          gap: 0.5,
        }}
      >
        {/* 名前（可変領域） */}
        <Box sx={{ flex: "1 1 auto", minWidth: 0 }}>
          <ListItemText
            primary={item.name}
            primaryTypographyProps={{
              noWrap: true,
              sx: {
                px: 0.5,
                borderRadius: 0.75,
                cursor: "default",
              },
            }}
          />
        </Box>
        {/* 目アイコン（固定幅） */}
        <Box sx={{ flex: "0 0 36px", display: "flex", justifyContent: "center" }}>
          <IconButton
            size="small"
            onClick={(e) => { e.stopPropagation(); onToggleVisible(item.id, !item.visible); }}
          >
            {item.visible ? <VisibilityIcon /> : <VisibilityOffIcon />}
          </IconButton>
        </Box>
        {/* ドラッグハンドル（固定幅・右端固定） */}
        <Box sx={{ flex: "0 0 32px", display: "flex", justifyContent: "flex-end" }}>
          <IconButton
            size="small"
            edge="end"
            {...attributes}
            {...listeners}
            onClick={(e) => e.stopPropagation()}
          >
            <DragIndicatorIcon fontSize="small" />
          </IconButton>
        </Box>
      </ListItemButton>
    </ListItem>
  );
}

export default function MapLayerPanel({
  items, onReorder, onToggleVisible, onAdd, onDelete,
  selectedId = null, onSelect,
  offset = { top: 12, right: 12 }, width: widthProp = 300, maxBodyHeight = 380,
  defaultOpen = false, zIndex
}: Props) {

  const translate = useTranslations("Config.mapImage");
  const [open, setOpen] = React.useState(defaultOpen);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } })
  );

  const handleEnd = (e: DragEndEvent) => {
    const { active, over } = e;
    if (!over || active.id === over.id) return;

    const aId = String(active.id);
    const oId = String(over.id);
    const oi = items.findIndex(i => i.id === aId);
    const ni = items.findIndex(i => i.id === oId);
    if (oi < 0 || ni < 0) return;

    onReorder(oi, ni);
  };

  return (
    <Box
      onPointerDown={(e) => e.stopPropagation()}
      onWheel={(e) => e.stopPropagation()}
      sx={{ position: "absolute", top: offset.top, right: offset.right, zIndex: zIndex ?? MAP_Z_INDEX.UI_OVERLAY }}
    >
      {/* 収納時は幅をタイトルに合わせる／展開時は指定width */}
      <Paper
        elevation={6}
        sx={{
          width: open ? widthProp : 100,
          overflow: "hidden",
        }}
      >
        {/* ヘッダ全体クリックで開閉 */}
        <Box
          role="button"
          aria-label={`${open ? "閉じる" : "開く"}`}
          tabIndex={0}
          onClick={() => setOpen((v) => !v)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              setOpen((v) => !v);
            }
          }}
          sx={{
            pl: 1,
            pr: 0,
            py: 0.5,
            display: "flex",
            alignItems: "center",
            gap: 1,
            borderBottom: open ? (t) => `1px solid ${t.palette.divider}` : "none",
            cursor: "pointer",
            userSelect: "none",
          }}
        >
          <MenuIcon fontSize="small" sx={{ color: (t) => (t.palette.mode === "dark" ? "#fff" : "#000") }} />
          <Box
            component="span"
            sx={{
              fontSize: 14,
              fontWeight: 400,
              color: (t) => (t.palette.mode === "dark" ? t.palette.common.white : "#000"),
              lineHeight: 1.6,
              px: 0,
            }}
          >
            {translate("title")}
          </Box>
        </Box>

        {/* 縦に展開 */}
        <Collapse in={open} timeout={220}>
          <Box sx={{ maxHeight: maxBodyHeight, overflow: "auto" }}>
            <DndContext sensors={sensors} onDragEnd={handleEnd}
              modifiers={[restrictToVerticalAxis, restrictToFirstScrollableAncestor]}>
              <SortableContext items={items.map(i => i.id)} strategy={verticalListSortingStrategy}>
                <List dense disablePadding>
                  {items.map(item => (
                    <Row
                      key={item.id}
                      item={item}
                      selected={selectedId === item.id}
                      onSelect={onSelect}
                      onToggleVisible={onToggleVisible}
                    />
                  ))}
                </List>
              </SortableContext>
            </DndContext>
          </Box>

          <Divider />

          <Box sx={{ p: 1, display: "flex", gap: 1, flexDirection: { xs: "column", sm: "row" } }}>
            <Button component="label" variant="outlined" startIcon={<AddIcon />} fullWidth>
              {translate("append")}
              <input hidden accept="image/*" type="file" onChange={onAdd} />
            </Button>
            <Button
              variant="contained" color="error" startIcon={<DeleteIcon />}
              disabled={!selectedId} onClick={() => selectedId && onDelete(selectedId)} fullWidth
            >
              {translate("remove")}
            </Button>
          </Box>
        </Collapse>
      </Paper>
    </Box>
  );
}
