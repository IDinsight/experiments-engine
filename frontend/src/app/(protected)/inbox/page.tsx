"use client";
import * as React from "react";
import { useState } from "react";
import { Button } from "@/components/catalyst/button";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Trash, MailOpen, MailIcon } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

import type { Message } from "./types";
import { getMessages, patchMessageReadStatus, deleteMessages } from "./api";
import { useAuth } from "@/utils/auth";

// Mock data for messages

export default function MessagePage() {
  const { token } = useAuth();

  React.useEffect(() => {
    getMessages({ token }).then((messages) => {
      const sortedMessages = [...messages].sort(sortMessagesByDate);
      setMessages(sortedMessages);
    });
  }, [token]);

  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedMessageIds, setSelectedMessageIds] = useState<number[]>([]);
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const sortMessagesByDate = (a: Message, b: Message) =>
    new Date(b.created_datetime_utc).getTime() -
    new Date(a.created_datetime_utc).getTime();

  const handleCheckboxChange = (messageId: number) => {
    setSelectedMessageIds((prev) =>
      prev.includes(messageId)
        ? prev.filter((id) => id !== messageId)
        : [...prev, messageId]
    );
  };

  const handleMessageClick = (message: Message) => {
    setSelectedMessage(message);
    setIsDrawerOpen(true);
    if (message.is_unread) {
      patchMessageReadStatus({
        token,
        message_ids: [message.message_id],
        is_unread: false,
      }).then((messages) => {
        const sortedMessages = [...messages].sort(sortMessagesByDate);
        setMessages(sortedMessages);
      });
    }
  };

  const handleDeleteSelected = () => {
    deleteMessages({ token, message_ids: selectedMessageIds }).then(
      (messages) => {
        const sortedMessages = [...messages].sort(sortMessagesByDate);
        setMessages(sortedMessages);
      }
    );
    setSelectedMessageIds([]);
    setSelectedMessage(null);
  };

  const handleToggleReadSelected = (markAsRead: boolean) => {
    patchMessageReadStatus({
      token,
      message_ids: selectedMessageIds,
      is_unread: !markAsRead,
    }).then((messages) => {
      const sortedMessages = [...messages].sort(sortMessagesByDate);
      setMessages(sortedMessages);
    });

    setSelectedMessageIds([]);
  };

  const getTimestampString = (timestamp: string) => {
    //Format the timestamp to say "today" or "yesterday" if applicable.
    // Always include time.
    const timeDifference = new Date().getTime() - new Date(timestamp).getTime();
    const daysDifference = timeDifference / (1000 * 3600 * 24);
    if (daysDifference < 1) {
      if (new Date(timestamp).getDate() === new Date().getDate()) {
        return `Today, ${new Date(timestamp).toLocaleString(undefined, {
          hour: "2-digit",
          minute: "2-digit",
        })}`;
      } else {
        return `Yesterday, ${new Date(timestamp).toLocaleString(undefined, {
          hour: "2-digit",
          minute: "2-digit",
        })}`;
      }
    } else {
      return new Date(timestamp).toLocaleString(undefined, {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    }
  };

  return (
    <div className="w-full p-4 min-h-screen flex flex-col">
      {/* Action Buttons */}
      <div className="mb-4 flex justify-between gap-2">
        <div className="flex gap-2">
          <Button
            outline
            onClick={() => handleToggleReadSelected(true)}
            disabled={selectedMessageIds.length === 0}
          >
            <MailIcon size={16} className="mr-2" />
            Read
          </Button>

          <Button
            outline
            onClick={() => handleToggleReadSelected(false)}
            disabled={selectedMessageIds.length === 0}
          >
            <MailOpen size={16} className="mr-2" />
            Unread
          </Button>
        </div>

        <Button
          onClick={handleDeleteSelected}
          disabled={selectedMessageIds.length === 0}
        >
          <Trash size={16} className="mr-2" />
          Delete
        </Button>
      </div>

      {/* Messages List */}
      <ScrollArea className="flex-grow border rounded-md dark:border-zinc-600">
        <div className="divide-y">
          {messages.map((message) => (
            <div
              key={message.message_id}
              className={`grid grid-cols-[auto_1fr_auto] gap-4 p-4 cursor-pointer hover:bg-gray-100 ${
                message.message_id === selectedMessage?.message_id
                  ? "bg-gray-100"
                  : ""
              }`}
              onClick={() => handleMessageClick(message)}
            >
              <div className="pt-1">
                <Checkbox
                  checked={selectedMessageIds.includes(message.message_id)}
                  onCheckedChange={() =>
                    handleCheckboxChange(message.message_id)
                  }
                  onClick={(e) => e.stopPropagation()}
                />
              </div>
              <div className="min-w-0">
                <div
                  className={`${
                    message.is_unread ? "font-bold" : "font-medium"
                  } truncate`}
                >
                  {message.title}
                </div>
                <p
                  className={`${
                    message.is_unread ? "font-bold" : "font-medium"
                  } text-sm text-gray-600 truncate`}
                >
                  {message.text}
                </p>
              </div>
              <div className="text-xs text-gray-500 w-38 text-right hidden md:block">
                {getTimestampString(message.created_datetime_utc)}
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Message Detail Drawer */}
      <Sheet open={isDrawerOpen} onOpenChange={setIsDrawerOpen}>
        <SheetContent className="w-screen sm:w-[400px]">
          {selectedMessage && (
            <>
              <SheetHeader>
                <SheetTitle>{selectedMessage.title}</SheetTitle>
              </SheetHeader>
              <div className="mt-4">
                <p className="text-sm text-gray-500 mb-4">
                  {new Date(
                    selectedMessage.created_datetime_utc
                  ).toLocaleString(undefined, {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
                <ScrollArea className="h-[calc(100vh-8rem)]">
                  <p className="text-gray-700">{selectedMessage.text}</p>
                </ScrollArea>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
