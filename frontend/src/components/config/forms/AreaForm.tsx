/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useCallback } from "react";
import { useFormContext, useFieldArray } from "react-hook-form";
import { useTranslations } from "next-intl";
import dynamic from "next/dynamic";
import { Button, Stack, Typography, Dialog, DialogActions, DialogTitle, DialogContent } from "@mui/material";
import { Close, Map } from '@mui/icons-material';
import { useDialogs, DialogProps } from "@toolpad/core/useDialogs";
import { AreaFormResponse } from "@/types/config";
import { FormProps } from "@/components/config/forms";

const MapView = dynamic(() => import("@/components/map/MapView"), { ssr: false });
const MapDraw = dynamic(() => import("@/components/map/MapDraw"), { ssr: false });

/** 地図ダイアログ */
function MapDialogComponent({ open, onClose, name, setValue, getValues }: DialogProps<{}> & { name: string; setValue: any; getValues: any }) {
  type Area = { name: string; vertex_list: number[][] }; // [lat, lng]
  const [tempAreas, setTempAreas] = useState<Area[]>(getValues(name) || []);
  const translate = useTranslations("Config");

  // GeoJSON -> Area[] に正規化（useCallbackで参照を固定）
  const geoToAreas = useCallback((shapes: any[]): Area[] => {
    return (shapes ?? []).map((shape) => ({
      name: (shape?.properties?.name ?? "").toString(),
      vertex_list: ((shape?.geometry?.coordinates?.[0] ?? []) as [number, number][])
        // GeoJSONは [lng, lat]、サーバ保存は [lat, lng]
        .map(([lng, lat]) => [lat, lng]),
    }));
  }, []);

  // MapDraw からの変更を常に Area[] に変換して保持（useCallbackで参照を固定）
  const handleMapChange = useCallback((geoShapes: any[]) => {
    setTempAreas(geoToAreas(geoShapes));
  }, [geoToAreas]);

  // フェイルセーフ：空配列で上書きしない（= 直前値を維持）
  const safeClose = useCallback(() => {
    setValue(name, tempAreas ?? [], { shouldDirty: true });
    onClose();
  }, [tempAreas, name, onClose, setValue]);

  return (
    <Dialog fullWidth maxWidth="lg" open={open} onClose={safeClose}>
      <DialogTitle>{translate("area.areaTitle")}</DialogTitle>
      <DialogContent sx={{ height: "600px", padding: 0 }}>
        <MapView style={{ width: "100%", height: "100%" }}>
          <MapDraw
            onChange={handleMapChange}
            initialShapes={getValues(name) || []}
          />
        </MapView>
      </DialogContent>
      <DialogActions sx={{ justifyContent: "flex-end", padding: "8px 16px" }}>
        <Button
          variant="outlined"
          color="primary"
          startIcon={<Close />}
          onClick={safeClose}>
          {translate("dialog.close")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

/**
 * エリアフォーム
 * @param name 設定名
 * @param form 設定内容
 * @param disabled 無効
 * @param validate 検証イベント
 */
export default function MapImageForm({ name, form }: FormProps<AreaFormResponse>) {
  const { control, getValues, setValue } = useFormContext();
  useFieldArray({
    control,
    name: name,
  });
  const translate = useTranslations("Config");
  const dialog = useDialogs();

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
      <Typography>{translate("area.text", {num: getValues(name)?.length || 0})}</Typography>
    </Stack>
  );
}
