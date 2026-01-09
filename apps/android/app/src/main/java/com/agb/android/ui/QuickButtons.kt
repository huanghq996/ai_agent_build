package com.agb.android.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun QuickButtons(onQuickInput: (String) -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        QuickButton("抽烟") { onQuickInput("抽烟一根") }
        QuickButton("骑车1.5") { onQuickInput("骑共享单车1.5元") }
    }
}

@Composable
fun QuickButton(text: String, onClick: () -> Unit) {
    OutlinedButton(onClick = onClick) {
        Text(text)
    }
}
