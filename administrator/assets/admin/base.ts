import "htmx.org";
import Alpine from "alpinejs";
import persist from "@alpinejs/persist";
import Chart from "chart.js/auto";
import { Colors } from "chart.js";

import "@fortawesome/fontawesome-free/css/all.css";
import "bootstrap/dist/js/bootstrap.bundle";
import "./css/base.scss";

window["htmx"] = require("htmx.org");

Alpine.plugin(persist);
Alpine.start();
window["Alpine"] = Alpine;

Chart.register(Colors);
window["Chart"] = Chart;
