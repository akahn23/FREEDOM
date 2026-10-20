/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { PageContainer } from '@toolpad/core/PageContainer';
import {
  Autocomplete,
  Box,
  Button,
  ButtonGroup,
  Checkbox,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Divider,
  FormControlLabel,
  IconButton,
  Menu,
  MenuItem,
  TextField,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  ArrowUpward,
  SearchOff,
  FilterAlt,
  Close,
  Update,
  SaveAlt,
  Search,
  ViewColumn,
} from '@mui/icons-material';
import { DateTime } from 'luxon';
import { TableVirtuoso, TableComponents } from 'react-virtuoso';
import { useTranslations } from 'next-intl';
import { useNotifications } from '@toolpad/core/useNotifications';
import { useDialogs } from '@toolpad/core/useDialogs';
import axios from '@/lib/axios';
import { LogEntry } from '@/types/log';


type Period = 'today' | 'yesterday' | '2days ago' | '3days' | '1week' | '1month';

type LogColumnDef = {
  field: keyof LogEntry;
  headerName: string;
  width?: number;
  renderCell?: (log: LogEntry, browserTimeZone: string) => React.ReactNode;
};

type SortDirection = 'asc' | 'desc' | null;

type SortModel = {
  field: keyof LogEntry | null;
  direction: SortDirection;
};

type SearchModel = {
  keywords: string[];
};

const DEFAULT_CHUNK_SIZE = 100; // 1回の追加取得件数
const FIXED_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] as const; // レベル絞り込みの固定候補
const MAX_TOOLTIP_CHARS = 5000; // ツールチップ表示の最大文字数
const MIN_COLUMN_WIDTH = 80; // 列幅の最小値(px)
const MAX_COLUMN_WIDTH = 1200; // 通常列の最大幅(px)
const MAX_MESSAGE_COLUMN_WIDTH = 200000; // Message列の最大幅(px)
const CELL_HORIZONTAL_PADDING = 20; // セル左右パディング分(px)
const CELL_BORDER_WIDTH = 1; // セル境界線分(px)
const CELL_AUTOFIT_BUFFER = 12; // 自動調整時の余白(px)
const HEADER_ACTIONS_WIDTH = 64; // ソート/操作ボタン分の幅(px)
const LEVEL_HEADER_EXTRA_WIDTH = 32; // Level列フィルタアイコン分の追加幅(px)

const LOG_COLUMN_WIDTHS: Record<keyof Pick<LogEntry, 'time' | 'name' | 'levelname' | 'message'>, number> = {
  time: 220,
  name: 180,
  levelname: 120,
  message: 580,
};

interface ManageColumnsMenuProps {
  columns: LogColumnDef[];
  columnVisibilityModel: Record<string, boolean>;
  setColumnVisibilityModel: (newModel: Record<string, boolean>) => void;
}

function ManageColumnsMenu(props: ManageColumnsMenuProps) {
  const { columns, columnVisibilityModel, setColumnVisibilityModel } = props;
  const t = useTranslations('Node.log.columnMenu');
  const [search, setSearch] = useState('');

  const visibleCount = columns.filter((col) => columnVisibilityModel[String(col.field)] !== false).length;

  const filteredColumns = columns.filter((col) => {
    const lower = search.toLowerCase();
    return col.headerName.toLowerCase().includes(lower) || String(col.field).toLowerCase().includes(lower);
  });

  const allVisible = filteredColumns.length > 0 && filteredColumns.every((col) => columnVisibilityModel[String(col.field)] !== false);

  return (
    <>
      <Box sx={{ px: 2, py: 1 }}>
        <TextField
          autoFocus
          size="small"
          placeholder={t('searchPlaceholder')}
          fullWidth
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.stopPropagation()}
        />
      </Box>
      {filteredColumns.map((col) => {
        const key = String(col.field);
        const isLastVisible = columnVisibilityModel[key] !== false && visibleCount <= 1;
        return (
          <MenuItem key={key} sx={{ p: 0 }}>
            <FormControlLabel
              sx={{ width: '100%', m: 0, px: 2, py: '6px' }}
              control={
                <Checkbox
                  checked={columnVisibilityModel[key] !== false}
                  disabled={isLastVisible}
                  onChange={() =>
                    setColumnVisibilityModel({
                      ...columnVisibilityModel,
                      [key]: !columnVisibilityModel[key],
                    })
                  }
                />
              }
              label={col.headerName}
            />
          </MenuItem>
        );
      })}
      <Divider />
      <MenuItem sx={{ p: 0 }}>
        <FormControlLabel
          sx={{ width: '100%', m: 0, px: 2, py: '6px' }}
          control={
            <Checkbox
              checked={allVisible}
              onChange={() => {
                const newModel = filteredColumns.reduce<Record<string, boolean>>((acc, col) => {
                  acc[String(col.field)] = true;
                  return acc;
                }, {});
                setColumnVisibilityModel({ ...columnVisibilityModel, ...newModel });
              }}
            />
          }
          label={t('selectAll')}
        />
      </MenuItem>
    </>
  );
}

function formatTime(raw: string, browserTimeZone: string): string {
  const normalized = raw.includes('T') ? raw : raw.replace(' ', 'T');
  const dt = DateTime.fromISO(normalized);
  if (!dt.isValid) return raw;
  return dt.setZone(browserTimeZone).toFormat('yyyy/MM/dd HH:mm:ss.SSS');
}

function normalizeKeywordItem(value: string): string {
  return value.trim().replace(/\s+/g, ' ');
}

function buildKeywordItems(items: string[], pendingInput = ''): string[] {
  const normalizedItems = [...items, pendingInput]
    .map(normalizeKeywordItem)
    .filter(Boolean);
  return Array.from(new Set(normalizedItems));
}

interface LevelFilterMenuProps {
  levels: string[];
  selection: Record<string, boolean>;
  onChange: (nextSelection: Record<string, boolean>) => void;
}

function LevelFilterMenu(props: LevelFilterMenuProps) {
  const { levels, selection, onChange } = props;
  const t = useTranslations('Node.log.levelFilterMenu');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const allChecked = levels.length > 0 && levels.every((level) => selection[level] !== false);

  return (
    <>
      <Tooltip title={t('tooltip')}>
        <IconButton
          size="small"
          onClick={(event) => {
            event.stopPropagation();
            setAnchorEl(event.currentTarget);
          }}
        >
          <FilterAlt fontSize="small" />
        </IconButton>
      </Tooltip>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
        disableAutoFocusItem
      >
        {levels.map((level) => (
          <MenuItem key={level} sx={{ p: 0 }}>
            <FormControlLabel
              sx={{ width: '100%', m: 0, px: 2, py: '6px' }}
              control={
                <Checkbox
                  checked={selection[level] !== false}
                  onChange={() => {
                    const next = { ...selection, [level]: !(selection[level] !== false) };
                    onChange(next);
                  }}
                />
              }
              label={level}
            />
          </MenuItem>
        ))}
        <Divider />
        <MenuItem sx={{ p: 0 }}>
          <FormControlLabel
            sx={{ width: '100%', m: 0, px: 2, py: '6px' }}
            control={
              <Checkbox
                checked={allChecked}
                onChange={() => {
                  const next: Record<string, boolean> = {};
                  levels.forEach((l) => { next[l] = !allChecked; });
                  onChange(next);
                }}
              />
            }
            label={t('selectAll')}
          />
        </MenuItem>
      </Menu>
    </>
  );
}

interface InlineDateEditProps {
  defaultStartDate: string;
  defaultStartTime: string;
  defaultEndDate: string;
  defaultEndTime: string;
  onUpdate: (params: { startDate: string; startTime: string; endDate: string; endTime: string }) => void;
}

const InlineDateEdit = React.memo(function InlineDateEdit(props: InlineDateEditProps) {
  const { defaultStartDate, defaultStartTime, defaultEndDate, defaultEndTime, onUpdate } = props;
  const t = useTranslations('Node.log.dateRange');
  const [localStartDate, setLocalStartDate] = useState(defaultStartDate);
  const [localStartTime, setLocalStartTime] = useState(defaultStartTime);
  const [localEndDate, setLocalEndDate] = useState(defaultEndDate);
  const [localEndTime, setLocalEndTime] = useState(defaultEndTime);

  useEffect(() => {
    setLocalStartDate(defaultStartDate);
    setLocalStartTime(defaultStartTime);
    setLocalEndDate(defaultEndDate);
    setLocalEndTime(defaultEndTime);
  }, [defaultStartDate, defaultStartTime, defaultEndDate, defaultEndTime]);

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, flexWrap: 'wrap' }}>
      <TextField label={t('startDate')} type="date" value={localStartDate} onChange={(e) => setLocalStartDate(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} size="small" />
      <TextField label={t('startTime')} type="time" value={localStartTime} onChange={(e) => setLocalStartTime(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} size="small" />
      <Typography variant="body1">～</Typography>
      <TextField label={t('endDate')} type="date" value={localEndDate} onChange={(e) => setLocalEndDate(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} size="small" />
      <TextField label={t('endTime')} type="time" value={localEndTime} onChange={(e) => setLocalEndTime(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} size="small" />
      <Button
        variant="text"
        startIcon={<Update />}
        onClick={() =>
          onUpdate({
            startDate: localStartDate,
            startTime: localStartTime,
            endDate: localEndDate,
            endTime: localEndTime,
          })
        }
      >
        {t('update')}
      </Button>
    </Box>
  );
});

export default function FreedomLogPage() {
  const isMounted = useRef(false);
  const virtuosoRef = useRef<any>(null);
  const browserTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const notifications = useNotifications();
  const dialogs = useDialogs();
  const translate = useTranslations('Node.log');

  const notificationsRef = useRef(notifications);
  useEffect(() => { notificationsRef.current = notifications; });

  const showError = useCallback((message: string) => {
    notificationsRef.current.show(message, {
      severity: 'error',
      autoHideDuration: 3000,
    });
  }, []);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  const [columnVisibilityModel, setColumnVisibilityModel] = useState<Record<string, boolean>>({
    time: true,
    name: true,
    levelname: true,
    message: true,
  });
  const [levelChecklistSelection, setLevelChecklistSelection] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    FIXED_LOG_LEVELS.forEach((level) => { initial[level] = true; });
    return initial;
  });

  const [searchModel, setSearchModel] = useState<SearchModel>({ keywords: [] });
  const [keywordDraftItems, setKeywordDraftItems] = useState<string[]>([]);
  const [keywordInput, setKeywordInput] = useState('');
  const [sortModel, setSortModel] = useState<SortModel>({ field: null, direction: null });

  const searchModelRef = useRef(searchModel);
  const sortModelRef = useRef(sortModel);
  const levelChecklistSelectionRef = useRef(levelChecklistSelection);
  useEffect(() => { searchModelRef.current = searchModel; }, [searchModel]);
  useEffect(() => { sortModelRef.current = sortModel; }, [sortModel]);
  useEffect(() => { levelChecklistSelectionRef.current = levelChecklistSelection; }, [levelChecklistSelection]);

  const initialDate: string = DateTime.local().toISODate() ?? '';
  const [selectedDate, setSelectedDate] = useState<string>(initialDate);
  const [activeRange, setActiveRange] = useState<{ begin_time: string; end_time: string } | null>(null);

  const [customStartDate, setCustomStartDate] = useState<string>(initialDate);
  const [customStartTime, setCustomStartTime] = useState<string>('00:00');
  const [customEndDate, setCustomEndDate] = useState<string>(initialDate);
  const [customEndTime, setCustomEndTime] = useState<string>('23:59');

  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [columnWidths, setColumnWidths] = useState<Record<keyof Pick<LogEntry, 'time' | 'name' | 'levelname' | 'message'>, number>>(LOG_COLUMN_WIDTHS);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLoadingMore, setIsLoadingMore] = useState<boolean>(false);
  const [hasMore, setHasMore] = useState<boolean>(true);
  const [nextCursorTime, setNextCursorTime] = useState<string | null>(null);

  const requestVersionRef = useRef(0);

  const defaultColumns: LogColumnDef[] = useMemo(
    () => [
      {
        field: 'time',
        headerName: translate('columns.time'),
        width: LOG_COLUMN_WIDTHS.time,
        renderCell: (log) => formatTime(log.time, browserTimeZone),
      },
      {
        field: 'name',
        headerName: translate('columns.name'),
        width: LOG_COLUMN_WIDTHS.name,
      },
      {
        field: 'levelname',
        headerName: translate('columns.level'),
        width: LOG_COLUMN_WIDTHS.levelname,
      },
      {
        field: 'message',
        headerName: translate('columns.message'),
        width: LOG_COLUMN_WIDTHS.message,
      },
    ],
    [browserTimeZone, translate]
  );

  const visibleColumns = useMemo(
    () =>
      defaultColumns
        .filter((col) => columnVisibilityModel[String(col.field)] !== false)
        .map((col) => ({
          ...col,
          width: columnWidths[col.field as keyof typeof columnWidths] ?? col.width ?? 200,
        })),
    [defaultColumns, columnVisibilityModel, columnWidths]
  );

  const totalMinWidth = useMemo(() => {
    if (!visibleColumns.length) return 400;
    return visibleColumns.reduce((sum, col) => sum + (col.width ?? 200), 0);
  }, [visibleColumns]);

  const resolveCurrentRange = useCallback(() => {
    if (activeRange) return activeRange;
    if (!selectedDate) return null;

    const dtLocal = DateTime.fromISO(selectedDate, { zone: 'local' });
    return {
      begin_time: dtLocal.startOf('day').toUTC().toISO() ?? '',
      end_time: dtLocal.endOf('day').toUTC().toISO() ?? '',
    };
  }, [activeRange, selectedDate]);

  const buildQueryPayload = useCallback(
    (range: { begin_time: string; end_time: string }, cursor?: string | null) => {
      const sel = levelChecklistSelectionRef.current;
      const sm = searchModelRef.current;
      const sort = sortModelRef.current;

      const activeLevels = Object.keys(sel).filter((k) => sel[k]);
      const direction = sort.direction ?? 'desc';

      return {
        begin_time: range.begin_time,
        end_time: range.end_time,
        cursor_time: cursor ?? null,
        row_count: DEFAULT_CHUNK_SIZE,
        keywords: sm.keywords.length ? sm.keywords : null,
        levelnames: activeLevels.length > 0 ? activeLevels : null,
        sort_field: sort.field ?? 'time',
        sort_direction: direction,
      };
    },
    []
  );

  const fetchLogChunk = useCallback(
    async (params: {
      begin_time: string;
      end_time: string;
      cursor_time?: string | null;
      row_count?: number;
      all_rows?: boolean;
      keywords?: string[] | null;
      levelnames?: string[] | null;
      sort_field?: keyof LogEntry | 'time';
      sort_direction?: 'asc' | 'desc';
    }) => {
      const kwargs: Record<string, unknown> = {
        begin_time: params.begin_time,
        end_time: params.end_time,
        cursor_time: params.cursor_time ?? null,
        keywords: params.keywords ?? null,
        levelnames: params.levelnames ?? null,
        sort_field: params.sort_field ?? 'time',
        sort_direction: params.sort_direction ?? 'desc',
      };
      if (params.all_rows) {
        kwargs.all_rows = true;
      } else if (typeof params.row_count === 'number') {
        kwargs.row_count = params.row_count;
      }

      const response = await axios.post('/node/freedom.log', {
        func: 'fetch',
        kwargs,
      });
      return Array.isArray(response.data) ? (response.data as LogEntry[]) : [];
    },
    []
  );

  const loadInitialLogs = useCallback(
    async (rangeOverride?: { begin_time: string; end_time: string }) => {
      const range = rangeOverride ?? resolveCurrentRange();
      if (!range) {
        showError(translate('errors.dateNotSelected'));
        return;
      }

      const reqVersion = ++requestVersionRef.current;
      setIsLoading(true);

      const activeLevels = Object.keys(levelChecklistSelectionRef.current).filter((k) => levelChecklistSelectionRef.current[k]);
      if (activeLevels.length === 0) {
        if (isMounted.current && reqVersion === requestVersionRef.current) {
          setLogs([]);
          setHasMore(false);
          setNextCursorTime(null);
          setIsLoading(false);
        }
        return;
      }

      try {
        const data = await fetchLogChunk(buildQueryPayload(range));
        if (!isMounted.current || reqVersion !== requestVersionRef.current) return;
        setLogs(data);
        setHasMore(data.length === DEFAULT_CHUNK_SIZE);
        setNextCursorTime(data.length ? data[data.length - 1].time : null);
      } catch (err: any) {
        if (!isMounted.current || reqVersion !== requestVersionRef.current) return;
        showError(err.response?.data?.error || translate('errors.loadLogsFailed'));
      } finally {
        if (isMounted.current && reqVersion === requestVersionRef.current) setIsLoading(false);
      }
    },
    [resolveCurrentRange, fetchLogChunk, showError, buildQueryPayload, translate]
  );

  const loadInitialLogsRef = useRef(loadInitialLogs);
  useEffect(() => { loadInitialLogsRef.current = loadInitialLogs; }, [loadInitialLogs]);

  const applySearchCriteria = useCallback(
    (
      nextSearchModel: SearchModel,
      nextLevelChecklistSelection: Record<string, boolean>,
      nextSortModel: SortModel,
    ) => {
      searchModelRef.current = nextSearchModel;
      levelChecklistSelectionRef.current = nextLevelChecklistSelection;
      sortModelRef.current = nextSortModel;

      setSearchModel(nextSearchModel);
      setLevelChecklistSelection(nextLevelChecklistSelection);
      setSortModel(nextSortModel);

      void loadInitialLogsRef.current();
    },
    []
  );

  const handleKeywordItemsChange = useCallback(
    (nextItems: string[]) => {
      const nextKeywords = buildKeywordItems(nextItems);
      setKeywordDraftItems(nextKeywords);
      setKeywordInput('');
      applySearchCriteria(
        { keywords: nextKeywords },
        levelChecklistSelectionRef.current,
        sortModelRef.current,
      );
    },
    [applySearchCriteria]
  );

  const updateSortModel = useCallback(
    (nextSort: SortModel) => {
      applySearchCriteria(searchModelRef.current, levelChecklistSelectionRef.current, nextSort);
    },
    [applySearchCriteria]
  );

  const measureTextWidth = useCallback((text: string) => {
    const ruler = document.createElement('span');
    ruler.textContent = text || '';
    ruler.style.position = 'absolute';
    ruler.style.visibility = 'hidden';
    ruler.style.pointerEvents = 'none';
    ruler.style.whiteSpace = 'nowrap';
    ruler.style.font = getComputedStyle(document.body).font;
    document.body.appendChild(ruler);
    const width = Math.ceil(ruler.getBoundingClientRect().width);
    document.body.removeChild(ruler);
    return width;
  }, []);

  const getDisplayTextForWidth = useCallback(
    (log: LogEntry, col: LogColumnDef) => {
      const raw = col.renderCell ? col.renderCell(log, browserTimeZone) : log[col.field];
      return String(raw ?? '');
    },
    [browserTimeZone]
  );

  const autoFitColumnWidth = useCallback(
    (field: keyof LogEntry) => {
      const scrollTop = scrollerRef.current?.scrollTop ?? null;
      const scrollLeft = scrollerRef.current?.scrollLeft ?? null;
      const col = defaultColumns.find((c) => c.field === field);
      if (!col) return;
      const headerActionWidth = HEADER_ACTIONS_WIDTH + (field === 'levelname' ? LEVEL_HEADER_EXTRA_WIDTH : 0);
      let maxWidth = measureTextWidth(col.headerName) + headerActionWidth;
      for (const row of logs) {
        maxWidth = Math.max(maxWidth, measureTextWidth(getDisplayTextForWidth(row, col)));
      }
      const maxWidthLimit = field === 'message' ? MAX_MESSAGE_COLUMN_WIDTH : MAX_COLUMN_WIDTH;
      const nextWidth = Math.min(
        maxWidthLimit,
        Math.max(
          MIN_COLUMN_WIDTH,
          Math.ceil(maxWidth) + CELL_HORIZONTAL_PADDING + CELL_BORDER_WIDTH + CELL_AUTOFIT_BUFFER,
        )
      );
      setColumnWidths((prev) => ({ ...prev, [field as keyof typeof prev]: nextWidth }));
      if (scrollTop !== null || scrollLeft !== null) {
        requestAnimationFrame(() => {
          if (!scrollerRef.current) return;
          if (scrollTop !== null) scrollerRef.current.scrollTop = scrollTop;
          if (scrollLeft !== null) scrollerRef.current.scrollLeft = scrollLeft;
        });
      }
    },
    [defaultColumns, logs, measureTextWidth, getDisplayTextForWidth]
  );

  const resizeStateRef = useRef<{ field: keyof LogEntry; startX: number; startWidth: number } | null>(null);
  const scrollerRef = useRef<HTMLDivElement | null>(null);

  const handleColumnResizeMouseDown = useCallback(
    (field: keyof LogEntry, event: React.MouseEvent<HTMLDivElement>) => {
      event.preventDefault();
      event.stopPropagation();
      resizeStateRef.current = {
        field,
        startX: event.clientX,
        startWidth: columnWidths[field as keyof typeof columnWidths] ?? 200,
      };
    },
    [columnWidths]
  );

  useEffect(() => {
    const onMouseMove = (event: MouseEvent) => {
      const state = resizeStateRef.current;
      if (!state) return;
      const delta = event.clientX - state.startX;
      const next = Math.min(MAX_COLUMN_WIDTH, Math.max(MIN_COLUMN_WIDTH, state.startWidth + delta));
      setColumnWidths((prev) => ({ ...prev, [state.field as keyof typeof prev]: next }));
    };
    const onMouseUp = () => { resizeStateRef.current = null; };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, []);

  const loadMoreLogs = useCallback(async () => {
    if (isLoading || isLoadingMore || !hasMore || !nextCursorTime) return;
    const range = resolveCurrentRange();
    if (!range) return;

    const reqVersion = requestVersionRef.current;
    setIsLoadingMore(true);

    try {
      const data = await fetchLogChunk({
        ...buildQueryPayload(range, nextCursorTime),
        cursor_time: nextCursorTime,
      });
      if (!isMounted.current || reqVersion !== requestVersionRef.current) return;

      setLogs((prev) => {
        const seen = new Set(prev.map((l) => l.time));
        const merged = [...prev];
        for (const row of data) {
          if (!seen.has(row.time)) merged.push(row);
        }
        return merged;
      });
      setHasMore(data.length === DEFAULT_CHUNK_SIZE);
      setNextCursorTime(data.length ? data[data.length - 1].time : null);
    } catch (err: any) {
      if (!isMounted.current || reqVersion !== requestVersionRef.current) return;
      showError(err.response?.data?.error || translate('errors.loadMoreLogsFailed'));
    } finally {
      if (isMounted.current && reqVersion === requestVersionRef.current) setIsLoadingMore(false);
    }
  }, [isLoading, isLoadingMore, hasMore, nextCursorTime, resolveCurrentRange, fetchLogChunk, showError, buildQueryPayload, translate]);

  useEffect(() => {
    if (!isMounted.current) return;
    void loadInitialLogsRef.current();
  }, []);

  const [csvModalOpen, setCsvModalOpen] = useState<boolean>(false);
  const handleCSVExport = async () => {
    const confirmed = await dialogs.confirm(
      translate('dialog.confirmCsvExport.content', {
        startDate: customStartDate,
        startTime: customStartTime,
        endDate: customEndDate,
        endTime: customEndTime,
      }),
      {
        title: translate('dialog.title'),
        okText: translate('dialog.confirmCsvExport.okText'),
        cancelText: translate('dialog.cancel'),
      }
    );
    if (!confirmed) return;

    setCsvModalOpen(true);
    try {
      const range = resolveCurrentRange();
      if (!range) {
        showError(translate('errors.dateNotSelected'));
        setCsvModalOpen(false);
        return;
      }

      const data = await fetchLogChunk({ ...range, all_rows: true });
      const exportColumns = visibleColumns.length ? visibleColumns : defaultColumns;
      const header = exportColumns.map((col) => col.headerName).join(',');
      const csvRows = data.map((row) =>
        exportColumns
          .map((col) => {
            const raw =
              col.field === 'time'
                ? formatTime(String(row.time ?? ''), browserTimeZone)
                : col.renderCell
                  ? col.renderCell(row, browserTimeZone)
                  : row[col.field];
            const value = String(raw ?? '').replace(/"/g, '""');
            return `"${value}"`;
          })
          .join(',')
      );

      const csvContent = [header, ...csvRows].join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);

      const fileName = customStartDate && customEndDate && customStartDate !== customEndDate
        ? `${customStartDate.replace(/-/g, '_')}-${customEndDate.replace(/-/g, '_')}-log.csv`
        : `${customStartDate.replace(/-/g, '_')}-log.csv`;

      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch {
      // noop
    } finally {
      setCsvModalOpen(false);
    }
  };

  const [selectedPeriodButton, setSelectedPeriodButton] = useState<Period | null>('today');

  const applyRangeAndReload = useCallback(
    async (begin: DateTime, end: DateTime) => {
      const newStartDate = begin.toISODate() ?? '';
      const newEndDate = end.toISODate() ?? '';
      const newStartTime = begin.toFormat('HH:mm');
      const newEndTime = end.toFormat('HH:mm');

      setSelectedDate(newStartDate);
      setCustomStartDate(newStartDate);
      setCustomStartTime(newStartTime);
      setCustomEndDate(newEndDate);
      setCustomEndTime(newEndTime);

      const beginUTC = begin.toUTC().toISO() ?? '';
      const endUTC = end.toUTC().toISO() ?? '';
      const nextRange = { begin_time: beginUTC, end_time: endUTC };
      setActiveRange(nextRange);
      await loadInitialLogs(nextRange);
    },
    [loadInitialLogs]
  );

  const handlePeriodSelect = async (period: Period) => {
    setSelectedPeriodButton(period);
    const now = DateTime.local();
    let begin = now.startOf('day');
    let end = now.endOf('day');

    switch (period) {
      case 'yesterday':
        begin = now.minus({ days: 1 }).startOf('day');
        end = now.minus({ days: 1 }).endOf('day');
        break;
      case '2days ago':
        begin = now.minus({ days: 2 }).startOf('day');
        end = now.minus({ days: 2 }).endOf('day');
        break;
      case '3days':
        begin = now.minus({ days: 2 }).startOf('day');
        end = now.endOf('day');
        break;
      case '1week':
        begin = now.minus({ days: 6 }).startOf('day');
        end = now.endOf('day');
        break;
      case '1month':
        begin = now.minus({ days: 29 }).startOf('day');
        end = now.endOf('day');
        break;
      default:
        break;
    }

    await applyRangeAndReload(begin, end);
  };

  const handleUpdateCustomRange = async ({ startDate, startTime, endDate, endTime }: { startDate: string; startTime: string; endDate: string; endTime: string }) => {
    const dtStartLocal = DateTime.fromISO(`${startDate}T${startTime}`, { zone: 'local' });
    const dtEndLocal = DateTime.fromISO(`${endDate}T${endTime}`, { zone: 'local' });

    if (dtEndLocal < dtStartLocal) {
      showError(translate('errors.endBeforeStart'));
      return;
    }

    const detectMatchingPeriod = (): Period | null => {
      const dtStartDayLocal = dtStartLocal.startOf('day');
      const dtEndDayLocal = dtEndLocal.endOf('day');
      const now = DateTime.local();
      const nowStart = now.startOf('day');
      const nowEnd = now.endOf('day');
      // today
      if (dtStartDayLocal.equals(nowStart) && dtEndDayLocal.equals(nowEnd)) {
        return 'today';
      }
      // yesterday
      const yesterdayStart = now.minus({ days: 1 }).startOf('day');
      const yesterdayEnd = now.minus({ days: 1 }).endOf('day');
      if (dtStartDayLocal.equals(yesterdayStart) && dtEndDayLocal.equals(yesterdayEnd)) {
        return 'yesterday';
      }
      // 2days ago
      const twoDaysAgoStart = now.minus({ days: 2 }).startOf('day');
      const twoDaysAgoEnd = now.minus({ days: 2 }).endOf('day');
      if (dtStartDayLocal.equals(twoDaysAgoStart) && dtEndDayLocal.equals(twoDaysAgoEnd)) {
        return '2days ago';
      }
      // 3days
      const threeDaysStart = now.minus({ days: 2 }).startOf('day');
      const threeDaysEnd = now.endOf('day');
      if (dtStartDayLocal.equals(threeDaysStart) && dtEndDayLocal.equals(threeDaysEnd)) {
        return '3days';
      }
      // 1week
      const oneWeekStart = now.minus({ days: 6 }).startOf('day');
      const oneWeekEnd = now.endOf('day');
      if (dtStartDayLocal.equals(oneWeekStart) && dtEndDayLocal.equals(oneWeekEnd)) {
        return '1week';
      }
      // 1month
      const oneMonthStart = now.minus({ days: 29 }).startOf('day');
      const oneMonthEnd = now.endOf('day');
      if (dtStartDayLocal.equals(oneMonthStart) && dtEndDayLocal.equals(oneMonthEnd)) {
        return '1month';
      }
      return null;
    };
    const detectedPeriod = detectMatchingPeriod();
    setSelectedPeriodButton(detectedPeriod);
    await applyRangeAndReload(dtStartLocal, dtEndLocal);
  };

  const tableKey = useMemo(
    () => visibleColumns.map((c) => String(c.field)).join(','),
    [visibleColumns]
  );

  const tableComponents = useMemo<TableComponents<LogEntry>>(
    () => ({
      Scroller: React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(function VirtuosoScroller(scrollerProps, ref) {
        const props = scrollerProps as React.HTMLAttributes<HTMLDivElement>;
        return (
          <div
            {...props}
            ref={(node) => {
              scrollerRef.current = node;
              if (typeof ref === 'function') {
                ref(node);
              } else if (ref) {
                ref.current = node;
              }
            }}
            style={{
              ...(props.style ?? {}),
              overflow: 'auto',
            }}
          />
        );
      }),
      Table: (tableProps) => (
        <table
          {...tableProps}
          style={{
            ...tableProps.style,
            borderSpacing: 0,
            minWidth: totalMinWidth,
            tableLayout: 'fixed',
          }}
        />
      ),
      TableHead: (headProps) => <thead {...headProps} style={{ position: 'sticky', top: 0, zIndex: 3, background: '#f7f7f7' }} />,
      TableRow: (rowProps) => <tr {...rowProps} />,
      TableBody: React.forwardRef<HTMLTableSectionElement>(function VirtuosoTableBody(bodyProps, ref) {
        return <tbody {...bodyProps} ref={ref} />;
      }),
    }),
    [totalMinWidth]
  );

  useEffect(() => {
    virtuosoRef.current?.scrollToIndex?.({ index: 0, align: 'start', behavior: 'auto' });
  }, [searchModel, sortModel, levelChecklistSelection]);

  const [anchorElColumns, setAnchorElColumns] = useState<null | HTMLElement>(null);
  const [hoveredSortField, setHoveredSortField] = useState<keyof LogEntry | null>(null);

  return (
    <PageContainer title={translate('name')}>
      <Toolbar disableGutters sx={{ mb: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', mb: 1, gap: 2, flexWrap: 'wrap' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            <Typography variant="body1">{translate('period.label')}</Typography>
            <ButtonGroup variant="outlined">
              <Button variant={selectedPeriodButton === 'today' ? 'contained' : 'outlined'} onClick={() => void handlePeriodSelect('today')}>{translate('period.today')}</Button>
              <Button variant={selectedPeriodButton === 'yesterday' ? 'contained' : 'outlined'} onClick={() => void handlePeriodSelect('yesterday')}>{translate('period.yesterday')}</Button>
              <Button variant={selectedPeriodButton === '2days ago' ? 'contained' : 'outlined'} onClick={() => void handlePeriodSelect('2days ago')}>{translate('period.twoDaysAgo')}</Button>
              <Button variant={selectedPeriodButton === '3days' ? 'contained' : 'outlined'} onClick={() => void handlePeriodSelect('3days')}>{translate('period.threeDays')}</Button>
              <Button variant={selectedPeriodButton === '1week' ? 'contained' : 'outlined'} onClick={() => void handlePeriodSelect('1week')}>{translate('period.oneWeek')}</Button>
              <Button variant={selectedPeriodButton === '1month' ? 'contained' : 'outlined'} onClick={() => void handlePeriodSelect('1month')}>{translate('period.oneMonth')}</Button>
            </ButtonGroup>
          </Box>
        </Box>
      </Toolbar>

      <InlineDateEdit
        defaultStartDate={customStartDate}
        defaultStartTime={customStartTime}
        defaultEndDate={customEndDate}
        defaultEndTime={customEndTime}
        onUpdate={(params) => void handleUpdateCustomRange(params)}
      />

      <Toolbar variant="dense" disableGutters sx={{ p: 1, gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
        <Tooltip title={translate('toolbar.columnManage')}>
          <IconButton onClick={(event) => setAnchorElColumns(event.currentTarget)}>
            <ViewColumn />
          </IconButton>
        </Tooltip>
        <Tooltip title={translate('toolbar.saveCsv')}>
          <IconButton onClick={() => void handleCSVExport()}>
            <SaveAlt />
          </IconButton>
        </Tooltip>

        <Autocomplete
          multiple
          freeSolo
          options={[]}
          value={keywordDraftItems}
          inputValue={keywordInput}
          onInputChange={(_, value) => setKeywordInput(value)}
          onChange={(_, value) => {
            handleKeywordItemsChange(value);
          }}
          sx={{ minWidth: 240, flex: '1 1 360px', maxWidth: 720 }}
          renderInput={(params) => (
            <TextField
              {...params}
              size="small"
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Search fontSize="small" />
                  <span>{translate('toolbar.keyword')}</span>
                </Box>
              }
            />
          )}
        />

        <Button
          variant="text"
          startIcon={<SearchOff />}
          onClick={async () => {
            const confirmed = await dialogs.confirm(translate('dialog.confirmClearConditions.content'), {
              title: translate('dialog.title'),
              okText: translate('dialog.confirmClearConditions.okText'),
              cancelText: translate('dialog.cancel'),
            });
            if (!confirmed) return;
            const resetLevelSelection: Record<string, boolean> = {};
            FIXED_LOG_LEVELS.forEach((level) => { resetLevelSelection[level] = true; });
            applySearchCriteria({ keywords: [] }, resetLevelSelection, { field: null, direction: null });
            setKeywordDraftItems([]);
            setKeywordInput('');
          }}
        >
          {translate('toolbar.clearConditions')}
        </Button>
      </Toolbar>

      <Menu
        anchorEl={anchorElColumns}
        open={Boolean(anchorElColumns)}
        onClose={() => setAnchorElColumns(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
        disableAutoFocusItem
      >
        <ManageColumnsMenu
          columns={defaultColumns}
          columnVisibilityModel={columnVisibilityModel}
          setColumnVisibilityModel={setColumnVisibilityModel}
        />
      </Menu>

      <Box sx={{ height: 500, width: '100%', border: '1px solid #ddd', borderRadius: 1, overflow: 'hidden', position: 'relative' }}>
        {isLoading && logs.length === 0 ? (
          <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <CircularProgress size={28} />
          </Box>
        ) : (
          <>
            <TableVirtuoso
              key={tableKey}
              ref={virtuosoRef}
              style={{ height: '100%', width: '100%' }}
              data={logs}
              endReached={() => {
                void loadMoreLogs();
              }}
              components={tableComponents}
              fixedHeaderContent={() => (
                <tr>
                  {visibleColumns.map((col) => {
                    const isSortField = sortModel.field === col.field;
                    const shouldShowSortButton = isSortField || hoveredSortField === col.field;
                    return (
                      <th
                        key={String(col.field)}
                        onMouseEnter={() => setHoveredSortField(col.field)}
                        onMouseLeave={() => setHoveredSortField((prev) => (prev === col.field ? null : prev))}
                        style={{
                          width: col.width,
                          minWidth: col.width,
                          maxWidth: col.width,
                          borderBottom: '1px solid #ddd',
                          borderRight: '1px solid #e0e0e0',
                          padding: '6px 10px',
                          textAlign: 'left',
                          background: '#f7f7f7',
                          position: 'relative',
                          userSelect: 'none',
                          boxSizing: 'border-box',
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: '2px' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            {col.field === 'levelname' ? (
                              <>
                                <span>{col.headerName}</span>
                                <LevelFilterMenu
                                  levels={[...FIXED_LOG_LEVELS]}
                                  selection={levelChecklistSelection}
                                  onChange={(nextSelection) =>
                                    applySearchCriteria(searchModelRef.current, nextSelection, sortModelRef.current)
                                  }
                                />
                              </>
                            ) : (
                              <span>{col.headerName}</span>
                            )}
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', minWidth: 56, justifyContent: 'flex-end' }}>
                            <Tooltip title={translate('table.sort')}>
                              <IconButton
                                size="small"
                                onClick={() => {
                                  const current = sortModelRef.current;
                                  if (current.field !== col.field) {
                                    updateSortModel({ field: col.field, direction: 'asc' });
                                  } else {
                                    updateSortModel({ field: col.field, direction: current.direction === 'asc' ? 'desc' : 'asc' });
                                  }
                                }}
                                color={isSortField ? 'primary' : 'default'}
                                sx={{
                                  visibility: shouldShowSortButton ? 'visible' : 'hidden',
                                }}
                              >
                                <ArrowUpward
                                  fontSize="inherit"
                                  sx={{
                                    transform: isSortField && sortModel.direction === 'desc' ? 'rotate(180deg)' : 'none',
                                    transition: 'transform 0.2s',
                                  }}
                                />
                              </IconButton>
                            </Tooltip>
                            {isSortField && (
                              <Tooltip title={translate('table.clearSort')}>
                                <IconButton size="small" onClick={() => updateSortModel({ field: null, direction: null })}>
                                  <Close fontSize="inherit" />
                                </IconButton>
                              </Tooltip>
                            )}
                          </Box>
                        </Box>
                        <div
                          onMouseDown={(e) => handleColumnResizeMouseDown(col.field, e)}
                          onDoubleClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            autoFitColumnWidth(col.field);
                          }}
                          style={{
                            position: 'absolute',
                            top: 0,
                            right: -4,
                            width: 8,
                            height: '100%',
                            cursor: 'col-resize',
                            zIndex: 10,
                            userSelect: 'none',
                          }}
                        />
                      </th>
                    );
                  })}
                </tr>
              )}
              itemContent={(_, log) =>
                visibleColumns.map((col) => {
                  const rawValue = col.renderCell ? col.renderCell(log, browserTimeZone) : log[col.field];
                  return (
                    <td
                      key={`${log.time}-${String(col.field)}`}
                      style={{
                        width: col.width,
                        minWidth: col.width,
                        maxWidth: col.width,
                        borderBottom: '1px solid #eee',
                        borderRight: '1px solid #f0f0f0',
                        padding: '8px 10px',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        boxSizing: 'border-box',
                      }}
                      title={((s: string) => s.length > MAX_TOOLTIP_CHARS ? s.slice(0, MAX_TOOLTIP_CHARS) + '…' : s)(String(rawValue ?? ''))}
                    >
                      {rawValue as React.ReactNode}
                    </td>
                  );
                })
              }
            />
            {logs.length === 0 && !isLoading && (
              <Box
                sx={{
                  position: 'absolute',
                  left: 0,
                  right: 0,
                  top: 45,
                  bottom: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  pointerEvents: 'none',
                }}
              >
                <Typography variant="body2" color="text.secondary">{translate('table.noData')}</Typography>
              </Box>
            )}
          </>
        )}

        {isLoadingMore && (
          <Box sx={{ position: 'absolute', bottom: 8, left: 0, right: 0, display: 'flex', justifyContent: 'center' }}>
            <CircularProgress size={18} />
          </Box>
        )}
      </Box>

      <Dialog open={csvModalOpen}>
        <DialogTitle>{translate('dialog.csvGenerating.title')}</DialogTitle>
        <DialogContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <CircularProgress size={24} />
          <DialogContentText>{translate('dialog.csvGenerating.content')}</DialogContentText>
        </DialogContent>
      </Dialog>
    </PageContainer>
  );
}
