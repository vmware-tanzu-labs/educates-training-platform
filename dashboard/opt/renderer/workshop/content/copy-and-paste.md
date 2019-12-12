Where the workshop instructions require you to enter an arbitrary text value into a web page or terminal rather than running it, it will be marked with the copy symbol <span class="fas fa-copy"></span> to indicate that clicking on it will copy it to your system paste buffer.

```copy
echo 'Copy to the system paste buffer'
```

Click on the highlighted code block above. The colour of the symbol should changed to indicate you clicked on it.

Now select one of the terminals to the right by clicking on the terminal area. The terminal cursor should be white and may also flash.

You can now paste the value to the terminal. How you paste the value to the terminals will depend on what web browser you are using, and what operating system.

For macOS users, you can use `<command-v>`.

For Windows and Linux users, try `<ctrl-v>` and if that doesn't work, try `<ctrl-shift-v>`.

For some web browsers you can also right click to bring up a context menu and select 'Paste'. In other browsers this doesn't work even though the 'Paste' option is shown. In this case, selecting the main 'Edit->Paste' menu of the browser does however work.

In some cases a value may need to be edited before being used. In this case, instead of being marked with the copy symbol, it will be marked with the user edit symbol <span class="fas fa-user-edit"></span>.

```copy-and-edit
echo 'Edit the value before using it'
```

When clicked, this will also result in the value being copied to the system paste buffer, but when pasted into the terminal or a web page, you should edit it as per any instructions provided in the workshop.

Where a command is marked to be run, but you would like to be able to copy the value so you can paste it into a separate web page or application, when clicking on the command, hold down the `<shift>` key first.

```execute
echo 'Hold the shift key when clicking'
```

So long as the `<shift>` key is held down when clicking, it will not be run in the terminal and instead will be copied to the system paste buffer.
