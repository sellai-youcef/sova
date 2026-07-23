import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import depthai as dai

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


class PerceptionNode(Node):
    def __init__(self):
        super().__init__('perception_node')

        self.searching = False
        self.target_label = None

        self.subscription_ = self.create_subscription(
            String, 'search_targets', self.target_callback, 10)
        self.coord_publisher_ = self.create_publisher(String, 'target_coordinates', 10)

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

        self.timer_ = None
        self.get_logger().info("perception node idle, waiting for a target")

    def target_callback(self, msg):
        self.target_label = msg.data
        self.searching = True
        self.get_logger().info(f"target received: {self.target_label}, starting search")

        if self.timer_ is None:
            self.timer_ = self.create_timer(0.2, self.check_detections)

    def check_detections(self):
        if not self.searching:
            return

        detections = self.detection_queue.get()
        for det in detections.detections:
            if det.confidence < CONFIDENCE_THRESHOLD:
                continue

            label_name = COCO_LABELS[det.label]
            if label_name == self.target_label:
                x = det.spatialCoordinates.x
                y = det.spatialCoordinates.y
                z = det.spatialCoordinates.z

                coord_msg = String()
                coord_msg.data = f"{x:.0f},{y:.0f},{z:.0f}"
                self.coord_publisher_.publish(coord_msg)

                self.get_logger().info(
                    f"found {label_name} at x={x:.0f}, y={y:.0f}, z={z:.0f}, published")

                self.searching = False
                self.get_logger().info("search complete")
                return


def main(args=None):
    rclpy.init(args=args)
    node = PerceptionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()