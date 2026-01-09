package com.agb.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.agb.android.ui.theme.AGBTheme
import com.agb.android.ui.RecordItem
import com.agb.android.ui.QuickButtons
import com.agb.android.ui.InputArea

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AGBTheme {
                MainScreen()
            }
        }
    }
}

@Composable
fun MainScreen() {
    var inputText by remember { mutableStateOf("") }
    val records = remember { mutableStateListOf<String>() }

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        LazyColumn(
            modifier = Modifier.weight(1f),
            reverseLayout = true
        ) {
            items(records) { record ->
                RecordItem(record)
            }
        }

        QuickButtons { text ->
            records.add(0, text)
        }

        Spacer(modifier = Modifier.height(8.dp))

        InputArea(
            text = inputText,
            onTextChange = { inputText = it },
            onSubmit = {
                if (inputText.isNotBlank()) {
                    records.add(0, inputText)
                    inputText = ""
                }
            }
        )
    }
}
