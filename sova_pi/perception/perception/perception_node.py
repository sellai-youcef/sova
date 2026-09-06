import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import depthai as dai
import time

COCO_LABELS = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
    "toothbrush"
]

CONFIDENCE_THRESHOLD = 0.6
LOST_TARGET_TIMEOUT = 10.0


class PerceptionNode(Node):
    def __init__(self):
        super().__init__('perception_node')

        self.state = "idle"
        self.target_label = None
        self.last_seen_time = None

        self.subscription_ = self.create_subscription(
            String, 'search_targets', self.target_callback, 10)
        self.coord_publisher_ = self.create_publisher(String, 'target_coordinates', 10)

        #publisher for horizontal offset 
        self.offset_publisher_ = self.create_publisher(String, 'target_offset', 10)
        self.device = dai.Device()
        self.pipeline = dai.Pipeline(self.device)

        cam_rgb = self.pipeline.create(dai.node.Camera).build()
        stereo = self.pipeline.create(dai.node.StereoDepth).build(
            autoCreateCameras=True,
            presetMode=dai.node.StereoDepth.PresetMode.FAST_ACCURACY
        )
        self.spatial_net = self.pipeline.create(dai.node.SpatialDetectionNetwork).build(
            cam_rgb, stereo, dai.NNModelDescription("luxonis/yolov6-nano:r2-coco-512x384")
        )
        self.detection_queue = self.spatial_net.out.createOutputQueue()

        self.pipeline.start()

        self.timer_ = self.create_timer(1.0, self.check_detections)
        self.get_logger().info("perception node idle, waiting for a target")

    def target_callback(self, msg):
        self.target_label = msg.data
        self.state = "searching"
        self.get_logger().info(f"target received: {self.target_label}, starting search")

    def check_detections(self):
        if self.state == "idle":
            return

        detections = self.detection_queue.get()
        found_this_frame = False

        for det in detections.detections:
            if det.confidence < CONFIDENCE_THRESHOLD:
                continue

            label_name = COCO_LABELS[det.label]
            if label_name == self.target_label:
                x = det.spatialCoordinates.x
                y = det.spatialCoordinates.y
                z = det.spatialCoordinates.z

                box_center = (det.xmin + det.xmax) / 2
                # offset ranges from -50 to 50 
                offset = (box_center - 0.5) * 100

                coord_msg = String()
                coord_msg.data = f"{x:.0f},{y:.0f},{z:.0f}"
                self.coord_publisher_.publish(coord_msg)

                offset_msg = String()
                offset_msg.data = f"{offset:.1f}"
                self.offset_publisher_.publish(offset_msg)

                found_this_frame = True
                self.last_seen_time = time.time()

                if self.state == "searching":
                    self.get_logger().info(
                        f"found {label_name}, now tracking, z={z:.0f}mm")
                    self.state = "tracking"
                elif self.state == "tracking":
                    self.get_logger().info(f"tracking {label_name}, z={z:.0f}mm")
                break

        if self.state == "tracking" and not found_this_frame:
            if time.time() - self.last_seen_time > LOST_TARGET_TIMEOUT:
                self.get_logger().info("lost target, back to searching")
                self.state = "searching"


def main(args=None):
    rclpy.init(args=args)
    node = PerceptionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()