package com.ledlink.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.ledlink.app.model.LedColorState

@Composable
fun ColorControls(
    state: LedColorState,
    onChange: (LedColorState) -> Unit,
    onPowerChange: (Boolean) -> Unit,
) {
    Column(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
        Row(modifier = Modifier.fillMaxWidth()) {
            Text("Power", modifier = Modifier.padding(top = 12.dp))
            Switch(checked = state.on, onCheckedChange = onPowerChange, modifier = Modifier.padding(start = 12.dp))
        }

        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(64.dp)
                .padding(vertical = 12.dp)
                .background(
                    Color(state.red, state.green, state.blue),
                    RoundedCornerShape(12.dp),
                )
        )

        ChannelSlider("Red", state.red) { onChange(state.copy(red = it)) }
        ChannelSlider("Green", state.green) { onChange(state.copy(green = it)) }
        ChannelSlider("Blue", state.blue) { onChange(state.copy(blue = it)) }
    }
}

@Composable
private fun ChannelSlider(label: String, value: Int, onValueChange: (Int) -> Unit) {
    Column {
        Text("$label: $value")
        Slider(
            value = value.toFloat(),
            onValueChange = { onValueChange(it.toInt()) },
            valueRange = 0f..255f,
        )
    }
}
