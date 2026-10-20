/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useCallback, useMemo, useRef, useState, useEffect } from "react";
import { useFormContext, useFieldArray, useWatch } from "react-hook-form";
import { useTranslations } from "next-intl";
import {
  Button,
  IconButton,
  Paper,
  Stack,
  Typography,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
} from "@mui/material";
import { Add, Delete } from "@mui/icons-material";
import { TableVirtuoso, TableComponents } from "react-virtuoso";
import { TableFormResponse } from "@/types/config";
import { FormProps, FormMap } from "@/components/config/forms";


/**
 * テーブルフォーム
 * @param name 設定名
 * @param form 設定内容
 * @param disabled 無効
 * @param validate 検証イベント
 */
export default function TableForm({ name, form, disabled, validate }: FormProps<TableFormResponse>) {
  const { control, watch, getValues } = useFormContext();
  const { fields, append, replace } = useFieldArray({ control, name });
  const items = useWatch({ control, name });
  const translate = useTranslations("Config");
  const scrollerRef = useRef<HTMLDivElement | null>(null);
  const [ height, setHeight ] = useState<number>(form.height ?? 400);
  const [ scrollbarHeight, setScrollbarHeight ] = useState(0);

  /**
   * 重複チェック
   * @todo 貫通して保存できてしまう問題
   * 動作が重いためコメントアウト
  */
  // useEffect(() => {
  //   if (!items) return;
  //   form.unique?.forEach((keyName) => {
  //     // 値ごとの出現回数を数える
  //     const counts = new Map<string, number>();
  //     items.forEach((item: any) => {
  //       const key = (item[keyName] ?? "").trim?.() ?? String(item[keyName] ?? "");
  //       if (!key) return;
  //       counts.set(key, (counts.get(key) || 0) + 1);
  //     });

  //     // 各行に対して重複エラーを設定・解除
  //     items.forEach((item: any, index: number) => {
  //       const key = (item[keyName] ?? "").trim?.() ?? String(item[keyName] ?? "");
  //       const count = counts.get(key) || 0;
  //       const conf = `${name}.${index}.${keyName}` as const;
  //       if (!key || count <= 1) {
  //         clearErrors(conf);
  //       } else {
  //         setError(conf, { type: "duplicate", message: translate("validate.duplicate") });
  //       }
  //     });
  //   });
  // }, [items, setError, clearErrors]);

  const indexById = useCallback(
    (id: string) => fields.findIndex((f) => f.id === id),
    [fields],
  );

  const removeById = useCallback(
    (id: string) => {
      const idx = indexById(id);
      if (idx < 0) return;
      const current = (getValues(name) ?? []) as any[];
      const next = current.filter((_, i) => i !== idx);
      replace(next);
    },
    [getValues, indexById, name, replace],
  );

  const VirtuosoTableComponents: TableComponents<any> = useMemo(
    () => ({
      Scroller: React.forwardRef<HTMLDivElement>(function VirtuosoScroller(props, ref) {
        return (
          <TableContainer {...props}
            ref={(node: HTMLDivElement | null) => {
              scrollerRef.current = node;

              if (typeof ref === 'function') {
                ref(node);
              } else if (ref) {
                ref.current = node;
              }
            }} component={Paper} variant="outlined"/>
        );
      }),
      Table: (props) => (
        <Table {...props} size="small" stickyHeader sx={{
          borderCollapse: 'separate',
          tableLayout: 'fixed',
          minWidth: "100%",
          width: form.width,
        }} />
      ),
      TableHead,
      TableRow: ({ item: _item, ...props }) => <TableRow {...props} />,
      TableBody: React.forwardRef<HTMLTableSectionElement>(function VirtuosoTableBody(props, ref) {
        return (
          <TableBody {...props} ref={ref} />
        );
      }),
    }),
    [form.width],
  );

  function fixedHeaderContent() {
    return (
      <TableRow>
        {Object.keys(form.forms).map((key) => (
          <TableCell key={`head-${key}`} variant="head" align="center" sx={{ fontWeight: 'bold' }}>
            {form.forms[key].label}
          </TableCell>
        ))}
        <TableCell key="head-actions" variant="head" align="center" sx={{ width: 80 }} />
      </TableRow>
    );
  }

  useEffect(() => {
    const measure = () => {
      if (scrollerRef.current) {
        const el = scrollerRef.current;
        const horizontalScrollbarHeight = el.offsetHeight - el.clientHeight;
        setScrollbarHeight(horizontalScrollbarHeight);
      }
    };
    measure();
    const resizeObserver = new ResizeObserver(() => {
      measure();
    });
    if (scrollerRef.current) resizeObserver.observe(scrollerRef.current);
    window.addEventListener('resize', measure);
    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('resize', measure);
    };
  }, []);

  return (
    <Stack spacing={1}>
      <Typography>{form.label}</Typography>
      <TableVirtuoso
        data={fields}
        components={VirtuosoTableComponents}
        totalListHeightChanged={height=>setHeight(height+scrollbarHeight+1)}
        followOutput={() => fields.length > items.length ? 'smooth' : false}
        style={{ height, maxHeight: form.height ?? 400}}
        computeItemKey={(_, item) => item.id}
        fixedHeaderContent={fixedHeaderContent}
        itemContent={(_, item) => {
          const index = indexById(item.id);
          if (index < 0) return null;
          const rowDisabled = disabled || !watch(`${name}.${index}.enable`, true);
          return (
            <>
              {Object.keys(form.forms).map((key) => {
                const FormComponent = FormMap[form.forms[key].type] as React.ComponentType<FormProps>;
                return (
                  <TableCell
                    key={`${item.id}.${index}.${key}`}
                    sx={{
                      bgcolor: rowDisabled ? "action.disabledBackground" : undefined,
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                    }}
                  >
                    <FormComponent
                      name={`${name}.${index}.${key}`}
                      form={{ ...form.forms[key], label: "" }}
                      disabled={disabled}
                      validate={validate}
                    />
                  </TableCell>
                );
              })}
              <TableCell
                key={`${item.id}.${index}.__actions`}
                align="center"
                sx={{
                  width: 80,
                  bgcolor: rowDisabled ? "action.disabledBackground" : undefined,
                }}
              >
                <IconButton
                  color="error"
                  disabled={disabled}
                  onClick={() => removeById(item.id)}
                >
                  <Delete />
                </IconButton>
              </TableCell>
            </>
          );
        }}
      />
      <Stack sx={{ alignItems: "flex-end" }}>
        <Button
          type="button"
          variant="outlined"
          disabled={disabled}
          sx={{ width: { xs: "100%", sm: "fit-content" } }}
          startIcon={<Add />}
          onClick={() => append(form.default)}
        >
          {translate("node.append")}
        </Button>
      </Stack>
    </Stack>
  );
}
