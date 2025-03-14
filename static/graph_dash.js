async function updateCharts() {
    const user = document.getElementById("pieUser").value;
    const year = document.getElementById("pieYear").value;
    const month = document.getElementById("pieMonth").value;

    try {
        let noData = false;

        // Update Bar Chart
        const barResponse = await fetch(`/plot/bar_chart/${year}/${month}?user=${encodeURIComponent(user)}`);
        const barData = await barResponse.json();
        if (barData.no_data) noData = true;
        else document.getElementById("barChart").src = "data:image/png;base64," + barData.bar_chart;

        // Update Stacked Bar Chart
        const stackedResponse = await fetch(`/plot/stacked_bar_chart/${year}/${month}`);
        const stackedData = await stackedResponse.json();
        if (stackedData.no_data) noData = true;
        else document.getElementById("stackedBarChart").src = "data:image/png;base64," + stackedData.stacked_bar_chart;

        // Update Line Chart
        await updateLineChart();  // Add this function call

        if (noData) {
            alert("Insufficient data available for the selected month and year.");
        }

    } catch (error) {
        console.error("Error updating charts:", error);
    }
}