/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo, useState } from "react";
import { useFormContext } from "react-hook-form";
import { useTranslations } from "next-intl";
import { Button, Dialog, DialogTitle, DialogContent, DialogActions, Stack, Typography, Box } from "@mui/material";
import { EditOutlined } from "@mui/icons-material";
import { DialogFormResponse } from "@/types/config";
import { FormProps, FormMap } from "@/components/config/forms";

/**
 * ダイアログフォーム
 * @param name 設定名
 * @param form 設定内容
 * @param disabled 無効
 * @param validate 検証イベント
 */
export default function DialogForm({ name, form, disabled, validate }: FormProps<DialogFormResponse>) {
  const { getValues, setValue, getFieldState, formState } = useFormContext();
  const translate = useTranslations("Config");

  const [open, setOpen] = useState(false);

  const fieldNames = useMemo(
    () => Object.keys(form.forms).map((key) => `${name}.${key}`),
    [name, form.forms]
  );

  /** 変更チェック */
  const isDirtyGroup = useMemo(() => {
    return fieldNames.some((fn) => getFieldState(fn, formState).isDirty);
  }, [fieldNames, getFieldState, formState]);

  const handleOpen = () => {
    const current = getValues(name);
    if ((current === undefined || current === null) && form.default) {
      setValue(name, form.default, { shouldDirty: false, shouldValidate: false });
    }
    setOpen(true);
  };

  const handleClose = () => setOpen(false);

  return (
    <Stack spacing={1}>
      <Stack direction="row" spacing={1} alignItems="center">
        <Typography>{form.label}</Typography>
        <Button
          type="button"
          variant="outlined"
          size="small"
          startIcon={<EditOutlined />}
          disabled={disabled}
          onClick={handleOpen}
        >
          {translate("dialog.change")}
        </Button>
        {isDirtyGroup && (
          <Typography variant="caption" color="warning.main" sx={{ fontWeight: 600 }}>
            {translate("dialog.dirty")}
          </Typography>
        )}
      </Stack>

      <Dialog
        open={open}
        onClose={handleClose}
        fullWidth={form.fullWidth ?? true}
        maxWidth={form.maxWidth ?? "sm"}
      >
        <DialogTitle>{form.label}</DialogTitle>

        <DialogContent dividers>
          <Stack spacing={2}>
            {Object.keys(form.forms).map((key, i) => {
              const FormComponent =
                FormMap[form.forms[key].type] as React.ComponentType<FormProps>;
              return (
                <Box key={`dialog-${name}-${i}`}>
                  <FormComponent
                    name={`${name}.${key}`}
                    form={form.forms[key]}
                    disabled={disabled}
                    validate={validate}
                  />
                </Box>
              );
            })}
          </Stack>
        </DialogContent>

        <DialogActions>
          <Button
            type="button"
            variant="contained"
            onClick={handleClose}
            disabled={disabled}
          >
            {translate("dialog.close")}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}