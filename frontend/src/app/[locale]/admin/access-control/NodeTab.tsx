/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

"use client";
import * as React from "react";
import {
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  Switch,
  TextField,
  Typography,
  Autocomplete,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Stack,
} from "@mui/material";
import { TableVirtuoso } from "react-virtuoso";
import { useTranslations } from "next-intl";


type NodeItem = {
  repository: string;
  node: string;
  node_id: string;
  label: string;
};

type FilterOption = {
  key: string;
  label: string;
  level: 0 | 1;
  kind: "all" | "type" | "class";
};

type TableCtx = {
  data: NodeItem[];
  onToggleRow: (index: number) => void;
  canEdit: boolean;
};

function keyOf(c: string, id: string) {
  return `${c}@@${id}`;
}

function normalizeText(s: string) {
  return (s ?? "").toLowerCase();
}

function displayNodeName(r: NodeItem) {
  const label = (r.label ?? "").trim();
  if (!label) return r.node_id;
  if (label.includes("/")) {
    const parts = label.split("/").map((s) => s.trim()).filter(Boolean);
    if (parts.length > 0) return parts[parts.length - 1];
  }
  return label;
}

const FILTER_ALL = "__all__";

const VirtuosoTableComponents = {
  Scroller: React.forwardRef<HTMLDivElement>(function VirtuosoScroller(props, ref) {
    return (
      <TableContainer component={Paper} variant="outlined" {...props} ref={ref} />
    );
  }),
  Table: (props: any) => (
    <Table
      {...props}
      size="small"
      sx={{
        borderCollapse: "separate",
        tableLayout: "fixed",
      }}
    />
  ),
  TableHead,
  TableRow: (props: any) => {
    const { context, ...rest } = props;
    const ctx = context as TableCtx | undefined;

    const index =
      typeof rest["data-index"] === "number" ? (rest["data-index"] as number) : null;
    const isBodyRow = index !== null && ctx;

    return (
      <TableRow
        {...rest}
        hover
        sx={{
          height: 44,
          cursor: isBodyRow && ctx.canEdit ? "pointer" : undefined,
        }}
        onClick={
          isBodyRow
            ? () => {
                if (!ctx.canEdit) return;
                ctx.onToggleRow(index);
              }
            : rest.onClick
        }
      />
    );
  },
  TableBody: React.forwardRef<HTMLTableSectionElement>(function VirtuosoTableBody(props, ref) {
    return (
      <TableBody {...props} ref={ref} />
    );
  }),
};

export default function NodeTab(props: {
  nodes: NodeItem[];
  allowed: Set<string>;
  canEdit: boolean;
  busy: boolean;
  onToggle: (r: NodeItem) => void;
  onBulkSelect: (list: NodeItem[]) => void;
  onBulkClear: (list: NodeItem[]) => void;
}) {
  const t = useTranslations("Admin.accessControl");
  const tNode = useTranslations("Node");

  const [filterKey, setFilterKey] = React.useState<string>(FILTER_ALL);
  const [searchText, setSearchText] = React.useState<string>("");
  const [debouncedSearchText, setDebouncedSearchText] = React.useState<string>("");
  const [showSelectedOnly, setShowSelectedOnly] = React.useState<boolean>(false);

  React.useEffect(() => {
    const id = setTimeout(() => setDebouncedSearchText(searchText), 200);
    return () => clearTimeout(id);
  }, [searchText]);

  const trType = React.useCallback(
    (type: string) => {
      try {
        return tNode(`${type}.name` as any);
      } catch {
        return type;
      }
    },
    [tNode]
  );

  const trClass = React.useCallback(
    (cls: string) => {
      try {
        return tNode(`${cls}.name` as any);
      } catch {
        return cls;
      }
    },
    [tNode]
  );

  const filterOptions = React.useMemo<FilterOption[]>(() => {
    const typeSet = new Set<string>();
    const classesByType = new Map<string, Set<string>>();
    for (const r of props.nodes) {
      const type = (r.repository ?? "").trim();
      if (type) typeSet.add(type);
      const cls = (r.node ?? "").trim();
      if (type && cls) {
        const head = cls.split(".")[0] ?? "";
        if (head === type) {
          if (!classesByType.has(type)) classesByType.set(type, new Set());
          classesByType.get(type)!.add(cls);
        }
      }
    }
    const types = Array.from(typeSet).sort((a, b) => trType(a).localeCompare(trType(b)));
    const opts: FilterOption[] = [{ key: FILTER_ALL, label: t("filter.all"), level: 0, kind: "all" }];
    for (const type of types) {
      opts.push({ key: `type:${type}`, label: trType(type), level: 0, kind: "type" });
      const clsSet = classesByType.get(type);
      if (!clsSet) continue;
      const clsList = Array.from(clsSet).sort((a, b) => trClass(a).localeCompare(trClass(b)));
      for (const cls of clsList) {
        opts.push({ key: `class:${cls}`, label: trClass(cls), level: 1, kind: "class" });
      }
    }
    return opts;
  }, [props.nodes, trType, trClass, t]);

  const selectedFilterOption = React.useMemo(() => {
    return (
      filterOptions.find((o) => o.key === filterKey) ??
      filterOptions[0] ??
      { key: FILTER_ALL, label: t("filter.all"), level: 0, kind: "all" }
    );
  }, [filterOptions, filterKey, t]);

  const filteredNodes = React.useMemo(() => {
    const q = normalizeText(debouncedSearchText.trim());
    const base = props.nodes.filter((r) => {
      if (filterKey !== FILTER_ALL) {
        if (filterKey.startsWith("type:")) {
          const tt = filterKey.slice("type:".length);
          if (r.repository !== tt) return false;
        } else if (filterKey.startsWith("class:")) {
          const cc = filterKey.slice("class:".length);
          if (r.node !== cc) return false;
        }
      }
      if (q.length > 0) {
        const hay = normalizeText(`${r.label} ${r.node_id} ${r.node} ${r.repository}`);
        if (!hay.includes(q)) return false;
      }
      return true;
    });
    if (!showSelectedOnly) return base;
    return base.filter((r) => props.allowed.has(keyOf(r.node, r.node_id)));
  }, [props.nodes, filterKey, debouncedSearchText, showSelectedOnly, props.allowed]);

  const fixedHeaderContent = React.useCallback(() => {
    const headCellSx = { backgroundColor: "background.paper" };
    const allowColSx = { ...headCellSx, width: 64, minWidth: 64, maxWidth: 64, px: 0.5 };
    return (
      <TableRow>
        <TableCell sx={headCellSx}>{t("table.name")}</TableCell>
        <TableCell sx={headCellSx}>{t("table.repository")}</TableCell>
        <TableCell sx={headCellSx}>{t("table.node")}</TableCell>
        <TableCell sx={allowColSx} align="center">
          {t("table.allow")}
        </TableCell>
      </TableRow>
    );
  }, [t]);

  const rowContent = React.useCallback(
    (_: number, r: NodeItem) => {
      const k = keyOf(r.node, r.node_id);
      const checked = props.allowed.has(k);

      const repositoryLabel = trType(r.repository);
      const nodeLabel = trClass(r.node);
      const allowCellSx = { width: 64, minWidth: 64, maxWidth: 64, px: 0.5 };

      return (
        <>
          <TableCell sx={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {displayNodeName(r)}
          </TableCell>
          <TableCell sx={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {repositoryLabel}
          </TableCell>
          <TableCell sx={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {nodeLabel}
          </TableCell>
          <TableCell align="center" sx={allowCellSx}>
            <Checkbox
              size="small"
              checked={checked}
              disabled={!props.canEdit}
              onClick={(e) => e.stopPropagation()}
              onChange={() => props.onToggle(r)}
            />
          </TableCell>
        </>
      );
    },
    [props.allowed, props.canEdit, props.onToggle, trType, trClass]
  );

  const context = React.useMemo<TableCtx>(
    () => ({
      data: filteredNodes,
      onToggleRow: (index: number) => {
        const r = filteredNodes[index];
        if (!r) return;
        props.onToggle(r);
      },
      canEdit: props.canEdit,
    }),
    [filteredNodes, props]
  );

  return (
    <Stack spacing={1.5} sx={{ height: "100%" }}>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} alignItems={{ sm: "center" }}>
        <TextField
          size="small"
          label={t("labels.search")}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          sx={{ width: { xs: "100%", sm: 320 } }}
          disabled={props.busy}
        />

        <Autocomplete
          options={filterOptions}
          value={selectedFilterOption}
          onChange={(_, v) => setFilterKey(v?.key ?? FILTER_ALL)}
          getOptionLabel={(o) => o.label}
          renderInput={(params) => <TextField {...params} label={t("labels.filter")} size="small" />}
          sx={{ width: { xs: "100%", sm: 360 } }}
          isOptionEqualToValue={(a, b) => a.key === b.key}
          renderOption={(p, option) => {
            const { key, ...rest } = p as any;
            return (
              <li key={key} {...rest}>
                <Box sx={{ pl: option.level === 1 ? 3 : 0, minWidth: 0 }}>
                  <Typography variant="body2" noWrap sx={{ fontWeight: option.level === 0 ? 700 : 400 }}>
                    {option.label}
                  </Typography>
                </Box>
              </li>
            );
          }}
          disabled={props.busy}
        />
      </Stack>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ ml: { sm: "auto" } }}>
        <FormControlLabel
          control={<Switch checked={showSelectedOnly} onChange={(e) => setShowSelectedOnly(e.target.checked)} />}
          label={t("labels.showSelectedOnly")}
          disabled={props.busy}
        />
        <Button variant="outlined" onClick={() => props.onBulkSelect(filteredNodes)} disabled={!props.canEdit || filteredNodes.length === 0}>
          {t("buttons.selectAll")}
        </Button>
        <Button variant="outlined" onClick={() => props.onBulkClear(filteredNodes)} disabled={!props.canEdit || filteredNodes.length === 0}>
          {t("buttons.clearAll")}
        </Button>
      </Stack>

      <Box sx={{ flex: 1, minHeight: 240 }}>
        <TableVirtuoso
          style={{ height: "100%" }}
          data={filteredNodes}
          context={context}
          components={VirtuosoTableComponents as any}
          computeItemKey={(_, r) => `${r.node}@@${r.node_id}`}
          fixedHeaderContent={fixedHeaderContent}
          itemContent={rowContent}
        />
      </Box>
    </Stack>
  );
}
