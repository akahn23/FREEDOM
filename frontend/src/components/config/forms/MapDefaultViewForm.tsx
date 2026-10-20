/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect } from "react";
import { useFormContext, useWatch } from "react-hook-form";
import { useTranslations } from "next-intl";
import dynamic from "next/dynamic";
import { Button, Stack, Dialog, DialogTitle, DialogContent, DialogActions, Typography } from "@mui/material";
import { Close, Map } from "@mui/icons-material";
import { useDialogs, DialogProps } from "@toolpad/core/useDialogs";
import { FormProps } from "@/components/config/forms";
import MapDefaultViewPanel from "@/components/map/MapDefaultViewPanel";
import { MAP_Z_INDEX } from "@/components/map/mapZIndex";

// window 読込待ち
const MapView = dynamic(() => import("@/components/map/MapView"), { ssr: false });

/** backend 構造と一致させた型 */
interface DefaultViewValue {
  center: [number, number]; // [lat, lng]
  zoom: number;
  rotate: number;
}

/** 地図初期表示位置設定ダイアログ */
function MapDefaultViewDialog({ open, onClose, setValue, getValues }: DialogProps<{}> & { setValue: any; getValues: any }) {
  const translate = useTranslations("Config");

  /**
   * LocationForm の tempMarker と同じ考え方：
   * form の値を一時 state にコピーして編集する
   */
  const [tempView, setTempView] = useState<DefaultViewValue>(() => {
    const v = getValues("default_view");
    return {
      center: Array.isArray(v?.center) ? v.center : [0, 0],
      zoom: typeof v?.zoom === "number" ? v.zoom : 0,
      rotate: typeof v?.rotate === "number" ? v.rotate : 0,
    };
  });

  useEffect(() => {
    if (open) {
      const v = getValues("default_view");
      setTempView({
        center: Array.isArray(v?.center) ? v.center : [0, 0],
        zoom: typeof v?.zoom === "number" ? v.zoom : 0,
        rotate: typeof v?.rotate === "number" ? v.rotate : 0,
      });
    }
  }, [open]);

  /** Dialog close 時に form へ反映 */
  const handleClose = () => {
    setValue("default_view", tempView, { shouldDirty: true });
    onClose();
  };

  return (
    <Dialog
      fullWidth
      maxWidth="lg"
      open={open}
      onClose={handleClose}
      sx={{
        zIndex: MAP_Z_INDEX.DIALOG,
      }}
    >
      <DialogTitle>
        {translate("defaultView.defaultViewTitle", { default: "初期表示位置" })}
      </DialogTitle>

      <DialogContent
        sx={{
          height: "600px",
          padding: 0,
          position: "relative",
        }}
      >
        <MapView
          style={{ width: "100%", height: "100%" }}
          center={tempView.center}
          zoom={tempView.zoom}
          rotate={tempView.rotate}
          onCenterChange={(c) =>
            setTempView((v) => {
              const nextLat = c.lat;
              const nextLng = c.lng;

              if (
                Math.abs(v.center[0] - nextLat) < 1e-9 &&
                Math.abs(v.center[1] - nextLng) < 1e-9
              ) {
                return v; // 同じ値なら更新しない（無限ループ防止）
              }

              return {
                ...v,
                center: [nextLat, nextLng],
              };
            })
          }
          onZoomChange={(z) =>
            setTempView((v) => {
              if (v.zoom === z) return v;
              return {
                ...v,
                zoom: z,
              };
            })
          }
          onRotateChange={(r) =>
            setTempView((v) => {
              if (Math.abs(v.rotate - r) < 1e-9) return v;
              return {
                ...v,
                rotate: r,
              };
            })
          }
        />

        {/* 右上の一覧パネル */}
        <MapDefaultViewPanel
          value={{
            lat: tempView.center[0],
            lng: tempView.center[1],
            zoom: tempView.zoom,
            rotation: tempView.rotate,
          }}
          onUpdate={(next) =>
            setTempView({
              center: [next.lat, next.lng],
              zoom: next.zoom,
              rotate: next.rotation,
            })
          }
        />
      </DialogContent>

      <DialogActions>
        <Button
          variant="outlined"
          startIcon={<Close />}
          onClick={handleClose}
        >
          {translate("dialog.close")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

/**
 * mapDefaultView フォーム
 */
export default function MapDefaultViewForm({ form }: FormProps) {
  const translate = useTranslations("Config");
  const dialog = useDialogs();
  const { getValues, control, setValue } = useFormContext();

  const watched = useWatch({ control, name: "default_view" });

  const lat = watched?.center?.[0] ?? 0;
  const lng = watched?.center?.[1] ?? 0;
  const zoom = watched?.zoom ?? 0;
  const rotation = watched?.rotate ?? 0;

  return (
    <Stack spacing={1}>
      <Typography>{form.label}</Typography>
      <Stack direction="row" spacing={1}  sx={{ justifyContent: "flex-start", alignItems: "center" }}>
        <Button
          variant="outlined"
          startIcon={<Map />}
          onClick={() =>
            dialog.open(
              (props) => (
                <MapDefaultViewDialog
                  {...props}
                  getValues={getValues}
                  setValue={setValue}
                />
              ),
              {},
            )
          }
        >
          {translate("defaultView.label")}
        </Button>
        <Typography sx={{ whiteSpace: 'pre-line' }}>
          {translate("defaultView.text", { lat: lat.toFixed(6), lng: lng.toFixed(6), zoom, rotation: rotation.toFixed(2) })}
        </Typography>
      </Stack>
    </Stack>
  );
}
