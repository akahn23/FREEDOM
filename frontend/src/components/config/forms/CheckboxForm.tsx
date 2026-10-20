/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import { Controller, useFormContext } from "react-hook-form";
import {
  Checkbox,
  FormControlLabel,
  FormGroup,
  FormHelperText,
} from "@mui/material";
import { CheckboxFormResponse } from "@/types/config";
import { FormProps } from "@/components/config/forms";


/**
 * チェックボックスフォーム
 * @param name 設定名
 * @param form 設定内容
 * @param disabled 無効
 * @param validate 検証イベント
 */
export default function CheckboxForm({ name, form, disabled, validate }: FormProps<CheckboxFormResponse>) {
  const { control } = useFormContext();

  return (
    <Controller
      name={name}
      control={control}
      rules={{
        validate: validate,
      }}
      render={({ field, fieldState }) => (
        <FormGroup>
          <FormControlLabel
            label={form.label}
            disabled={disabled}
            control={
              <Checkbox
                checked={!!field.value}
                onChange={(e) => field.onChange(e.target.checked)}
                name={field.name}
                slotProps={{ input: { ref: field.ref } }}
              />
            }
          />
          {!!fieldState.error && (
            <FormHelperText>{fieldState.error?.message}</FormHelperText>
          )}
        </FormGroup>
      )}
    />
  );
}
