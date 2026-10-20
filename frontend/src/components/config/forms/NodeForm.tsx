/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import { useFormContext, useFieldArray, useWatch } from "react-hook-form";
import { useTranslations } from "next-intl";
import { Button, Grid, Paper, Stack, Typography } from "@mui/material";
import { Add, Delete } from "@mui/icons-material";
import { NodeFormResponse } from "@/types/config";
import { FormProps, FormMap } from "@/components/config/forms";


/**
 * ノードフォーム
 * @param name 設定名
 * @param form 設定内容
 * @param disabled 無効
 * @param validate 検証イベント
 */
export default function NodeForm({ name, form, disabled, validate }: FormProps<NodeFormResponse>) {
  const { control, watch } = useFormContext();
  const { fields, append, remove } = useFieldArray({ control, name: name});
  useWatch({ control, name: name });
  const translate = useTranslations("Config");

  /**
   * 重複チェック
   * @todo 貫通して保存できてしまう問題
   * 動作が重いためコメントアウト
  */
  // useEffect(() => {
  //   if (!items) return;
  //   form.unique?.forEach(value => {
  //     // 値ごとの出現回数を数える
  //     const counts = new Map<string, number>();
  //     items.forEach((item: any) => {
  //       const key = (item[value] ?? "").trim();
  //       if (!key) return;
  //       counts.set(key, (counts.get(key) || 0) + 1);
  //     });

  //     // 各行に対して重複エラーを設定・解除
  //     items.forEach((item:any, index:number) => {
  //       const key = (item[value] ?? "").trim();
  //       const count = counts.get(key) || 0;
  //       const conf = `${name}.${index}.${value}` as const;
  //       if (!key || count <= 1) {
  //         clearErrors(conf);
  //       } else {
  //         setError(conf, { type: "duplicate", message: translate("validate.duplicate") });
  //       }
  //     });
  //   })
  // }, [items, setError, clearErrors]);

  return (
      <Stack spacing={1}>
        <Typography>{form.label}</Typography>
        <Grid container spacing={2}>
          {fields.map((item, index) => (
            <Grid key={item.id} size={{ xs: 12, md: 12 / Math.max(1, Math.min(12, form.columns ?? 3)) }}>
              <Paper
                variant="outlined"
                sx={ disabled || !watch(`${name}.${index}.enable`, true)
                  ? { bgcolor: 'action.disabledBackground' }
                  : undefined
                }>
                <Stack spacing={1} sx={{ py:2, px: 2 }}>
                  {Object.keys(form.forms).map((key, i) => {
                    const FormComponent = FormMap[form.forms[key].type] as React.ComponentType<FormProps>;
                    return (
                      <FormComponent
                        key={`${item.id}.${i}`}
                        name={`${name}.${index}.${key}`}
                        form={form.forms[key]}
                        disabled={disabled}
                        validate={validate}
                      />
                    );
                  })}
                  <Stack sx={{alignItems: "flex-end"}}>
                    <Button
                      type="button"
                      variant="text"
                      disabled={disabled}
                      startIcon={<Delete />}
                      onClick={() => remove(index)}
                    >
                      {translate("node.remove")}
                    </Button>
                  </Stack>
                </Stack>
              </Paper>
            </Grid>
          ))}
        </Grid>
        <Stack sx={{ alignItems: "flex-end" }}>
          <Button
            type="button"
            variant="outlined"
            disabled={disabled}
            sx={{
              width: { xs: '100%', sm: 'fit-content' },
            }}
            startIcon={<Add />}
            onClick={() => append(form.default)}
          >
            {translate("node.append")}
          </Button>
        </Stack>
      </Stack>
  );
}
