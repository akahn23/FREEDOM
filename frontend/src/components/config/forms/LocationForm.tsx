/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from "react";
import { useFormContext, useFieldArray } from "react-hook-form";
import { useTranslations } from "next-intl";
import dynamic from "next/dynamic";
import { Button, Stack, Typography, Dialog, DialogActions, DialogTitle, DialogContent } from "@mui/material";
import { Close, Map } from '@mui/icons-material';
import { useDialogs, DialogProps } from "@toolpad/core/useDialogs";
import { LocationFormResponse } from "@/types/config";
import { FormProps } from "@/components/config/forms";

const MapView = dynamic(() => import("@/components/map/MapView"), { ssr: false });
const MapDrawMarker = dynamic(() => import("@/components/map/MapDrawMarker"), { ssr: false });

/** 地図ダイアログ */
function MapDialogComponent({ open, onClose, name, setValue, getValues }: DialogProps<{}> & { name: string; setValue: any; getValues: any }) {
  const translate = useTranslations("Config");

  // 単一マーカー仕様に統一（既存値が配列ならそのまま採用）
  const [tempMarker, setTempMarker] = useState<any | null>(() => {
    const v = getValues(name);
    return v ?? null;
  });

  // GeoJSON(Point) → backend形式（配列 [lat, lng]）
  const convertMarkerToLocation = (m: any | null) => {
    if (!m) return null;
    const [lng, lat] = m.geometry.coordinates;
    return [lat, lng]; // ←ここを配列に変更
  };

  // 初期値を MapDrawMarker 用に整形
  const initialMarkerForMap = (() => {
    const v = getValues(name);
    if (!v || !Array.isArray(v)) return undefined;
    return { name: "位置", lat: v[0], lng: v[1] };
  })();

  return (
    <Dialog fullWidth maxWidth="lg" open={open} onClose={() => {
      const converted = convertMarkerToLocation(tempMarker);
      setValue(name, converted, { shouldDirty: true });
      onClose();
    }}>
      <DialogTitle>{translate("location.locationTitle")}</DialogTitle>
      <DialogContent sx={{ height: "600px", padding: 0 }}>
        <MapView style={{ width: "100%", height: "100%" }}>
          <MapDrawMarker
            onChange={setTempMarker}
            initialMarker={initialMarkerForMap}
          />
        </MapView>
      </DialogContent>
      <DialogActions sx={{ justifyContent: "flex-end", padding: "8px 16px" }}>
        <Button
          variant="outlined"
          color="primary"
          startIcon={<Close />}
          onClick={() => {
            const converted = convertMarkerToLocation(tempMarker);
            setValue(name, converted, { shouldDirty: true });
            onClose();
          }}
        >
          {translate("dialog.close")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

/**
 * ロケーションフォーム
 * @param name 設定名
 * @param form 設定内容
 * @param disabled 無効
 * @param validate 検証イベント
 */
export default function MapImageForm({ name, form }: FormProps<LocationFormResponse>) {
  const { control, getValues, setValue } = useFormContext();
  useFieldArray({
    control,
    name: name,
  });
  const translate = useTranslations("Config");
  const dialog = useDialogs();

  // 現在の位置情報を取得（配列形式）
  const current = getValues(name);
  const lat = Array.isArray(current) ? current[0] : 0.0;
  const lng = Array.isArray(current) ? current[1] : 0.0;

  return (
    <Stack direction="row" spacing={1}  sx={{ justifyContent: "flex-start", alignItems: "center" }}>
      <Button
        component="label"
        variant="outlined"
        startIcon={<Map/>}
        onClick={() => dialog.open((props) => <MapDialogComponent {...props} name={name} setValue={setValue} getValues={getValues} />, {})}
      >
        {form.label}
      </Button>
      <Typography sx={{ whiteSpace: 'pre' }}>
        {translate("location.text", { lat: lat.toFixed(6), lng: lng.toFixed(6) })}
      </Typography>
    </Stack>
  );
}
