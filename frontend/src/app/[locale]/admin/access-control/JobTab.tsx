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
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from "@mui/material";
import { TableVirtuoso } from "react-virtuoso";
import { useTranslations } from "next-intl";


type TableCtx = {
  data: string[];
  onToggleRow: (index: number) => void;
  canEdit: boolean;
};

function normalizeText(s: string) {
  return (s ?? "").toLowerCase();
}

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

export default function JobTab(props: {
  jobNames: string[];
  allowed: Set<string>;
  canEdit: boolean;
  busy: boolean;
  onToggle: (jobName: string) => void;
  onBulkSelect: (list: string[]) => void;
  onBulkClear: (list: string[]) => void;
}) {
  const t = useTranslations("Admin.accessControl");

  const [searchText, setSearchText] = React.useState<string>("");
  const [debouncedSearchText, setDebouncedSearchText] = React.useState<string>("");
  const [showSelectedOnly, setShowSelectedOnly] = React.useState<boolean>(false);

  React.useEffect(() => {
    const id = setTimeout(() => setDebouncedSearchText(searchText), 200);
    return () => clearTimeout(id);
  }, [searchText]);

  const filteredJobs = React.useMemo(() => {
    const q = normalizeText(debouncedSearchText.trim());
    const base = props.jobNames.filter((name) => {
      if (!q) return true;
      return normalizeText(name).includes(q);
    });
    if (!showSelectedOnly) return base;
    return base.filter((name) => props.allowed.has(name));
  }, [props.jobNames, debouncedSearchText, showSelectedOnly, props.allowed]);

  const fixedHeaderContent = React.useCallback(() => {
    const headCellSx = { backgroundColor: "background.paper" };
    const allowColSx = { ...headCellSx, width: 64, minWidth: 64, maxWidth: 64, px: 0.5 };
    return (
      <TableRow>
        <TableCell sx={headCellSx}>{t("jobTable.jobName")}</TableCell>
        <TableCell sx={allowColSx} align="center">
          {t("jobTable.allow")}
        </TableCell>
      </TableRow>
    );
  }, [t]);

  const rowContent = React.useCallback(
    (_: number, name: string) => {
      const checked = props.allowed.has(name);
      const allowCellSx = { width: 64, minWidth: 64, maxWidth: 64, px: 0.5 };

      return (
        <>
          <TableCell sx={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {name}
          </TableCell>
          <TableCell align="center" sx={allowCellSx}>
            <Checkbox
              size="small"
              checked={checked}
              disabled={!props.canEdit}
              onClick={(e) => e.stopPropagation()}
              onChange={() => props.onToggle(name)}
            />
          </TableCell>
        </>
      );
    },
    [props.allowed, props.canEdit, props.onToggle]
  );

  const context = React.useMemo<TableCtx>(
    () => ({
      data: filteredJobs,
      onToggleRow: (index: number) => {
        const name = filteredJobs[index];
        if (!name) return;
        props.onToggle(name);
      },
      canEdit: props.canEdit,
    }),
    [filteredJobs, props]
  );

  return (
    <Stack spacing={1.5} sx={{ height: "100%" }}>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} alignItems={{ sm: "center" }}>
        <TextField
          size="small"
          label={t("job.labels.search")}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          sx={{ width: { xs: "100%", sm: 320 } }}
          disabled={props.busy}
        />
      </Stack>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ ml: { sm: "auto" } }}>
        <FormControlLabel
          control={<Switch checked={showSelectedOnly} onChange={(e) => setShowSelectedOnly(e.target.checked)} />}
          label={t("job.labels.showSelectedOnly")}
          disabled={props.busy}
        />
        <Button variant="outlined" onClick={() => props.onBulkSelect(filteredJobs)} disabled={!props.canEdit || filteredJobs.length === 0}>
          {t("buttons.selectAll")}
        </Button>
        <Button variant="outlined" onClick={() => props.onBulkClear(filteredJobs)} disabled={!props.canEdit || filteredJobs.length === 0}>
          {t("buttons.clearAll")}
        </Button>
      </Stack>

      <Box sx={{ flex: 1, minHeight: 240 }}>
        <TableVirtuoso
          style={{ height: "100%" }}
          data={filteredJobs}
          context={context}
          components={VirtuosoTableComponents as any}
          computeItemKey={(_, name) => `job@@${name}`}
          fixedHeaderContent={fixedHeaderContent}
          itemContent={rowContent}
        />
      </Box>
    </Stack>
  );
}
