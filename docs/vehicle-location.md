# 车辆位置追踪

后端为每辆车保存最近一次 WGS84 位置和独立的上报、接收时间。超过 15 秒的位置标为 stale；乱序或重复时间的上报不覆盖新位置。时间必须带时区，未来超过 30 秒的上报会被拒绝。

## 接口

`GET /api/tasks/{task_id}/location` 使用现有用户 Bearer Token。普通用户仅能查看自己的任务，管理员可查看全部。返回 task_id、car_number、latitude、longitude、reported_at、received_at、is_stale 和 state。状态包括 unassigned、waiting、live、stale、inactive。任务结束或车辆已执行其他任务时不返回车辆位置，避免泄露后续行程。

管理员可通过现有 `PATCH /api/cars/{car_id}/location` 更新定位，也会同步独立的位置时间。

## 控制连接

服务端环境变量 `CAR_CONTROL_TOKEN_1` 为 ID=1 的车辆配置专用令牌，其他车辆按 ID 配置。连接 `/ws/cars/1/control` 时必须携带 `Authorization: Bearer <令牌>` 请求头。未配置令牌、令牌错误或车辆未启用时拒绝连接。该校验也适用于既有调度、完成回传连接。生产连接应使用 WSS，令牌不放在前端或 URL 中。

```json
{
  "type": "location_update",
  "latitude": 30.7566,
  "longitude": 103.9884,
  "coord_system": "WGS84",
  "reported_at": "2026-09-18T07:00:00Z",
  "speed": 1.2
}
```

speed 可选，沿用车辆字段单位 km/h。返回 location_update_ack，ok 表示消息有效，accepted=false 表示乱序或重复上报被忽略。

## 前端

通过当前用户的有效预约关联快递、任务。位置弹窗打开且首页聚焦、App 在前台时查询位置，每次完成后间隔 2 秒再次请求。请求超时 5 秒；离开前台、关闭或切换用户任务时取消旧请求。刷新失败显示提示，并保留最近位置。

地图使用现有 react-native-maps 默认 provider，接收 WGS84 坐标；GCJ-02 的任务目的地使用已有转换函数。拖动地图暂停跟随，定位按钮恢复。默认地图底图在 Android 上的实际可用性仍取决于项目的原生地图配置和设备服务支持。

应用启动的 create_all 会创建新 car_locations 表；使用迁移管理的数据库需执行新增迁移 8db92c8e4110，该迁移兼容已由 create_all 创建的表。WebSocket 连接仍在进程内，继续使用单 worker。
