/**
 * Drag & Drop and Touch Reorder Composable
 * Handles desktop drag-and-drop and touch-based reordering of lists
 */
import { ref } from 'vue'

export function useDragReorder(onReorder) {
  const dragIndex = ref(null)
  const dragOverIndex = ref(null)
  let touchStartIndex = null

  const handleDragStart = (event, index) => {
    dragIndex.value = index
    if (event?.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move'
      event.dataTransfer.setData('text/plain', index.toString())
    }
  }

  const handleDragEnd = () => {
    dragIndex.value = null
    dragOverIndex.value = null
    touchStartIndex = null
  }

  const handleDragOver = (event, index) => {
    if (event) {
      event.preventDefault()
      if (event.dataTransfer) {
        event.dataTransfer.dropEffect = 'move'
      }
    }
    dragOverIndex.value = index
  }

  const handleDrop = async (event, toIndex, items) => {
    if (event) event.preventDefault()
    let fromIndex = dragIndex.value
    if ((fromIndex === null || isNaN(fromIndex)) && event?.dataTransfer) {
      const raw = event.dataTransfer.getData('text/plain')
      if (raw !== '') fromIndex = parseInt(raw, 10)
    }

    if (fromIndex === null || isNaN(fromIndex) || fromIndex === toIndex || !items) {
      handleDragEnd()
      return null
    }

    const reordered = [...items]
    const [movedItem] = reordered.splice(fromIndex, 1)
    reordered.splice(toIndex, 0, movedItem)

    handleDragEnd()

    if (onReorder) {
      await onReorder(reordered, fromIndex, toIndex)
    }

    return reordered
  }

  // Touch reordering handlers
  const handleTouchStart = (event, index) => {
    touchStartIndex = index
    dragIndex.value = index
    dragOverIndex.value = index
  }

  const handleTouchMove = (event) => {
    const touch = event.touches?.[0]
    if (!touch || touchStartIndex === null) return

    if (event.cancelable) event.preventDefault()

    const targetEl = document.elementFromPoint(touch.clientX, touch.clientY)
    const itemEl = targetEl?.closest('[data-track-index]')
    if (itemEl && itemEl.dataset.trackIndex !== undefined) {
      const targetIndex = parseInt(itemEl.dataset.trackIndex, 10)
      if (!isNaN(targetIndex)) {
        dragOverIndex.value = targetIndex
      }
    }
  }

  const handleTouchEnd = async (items) => {
    const fromIndex = touchStartIndex
    const toIndex = dragOverIndex.value
    touchStartIndex = null

    if (fromIndex === null || toIndex === null || isNaN(fromIndex) || isNaN(toIndex) || fromIndex === toIndex || !items) {
      handleDragEnd()
      return null
    }

    const reordered = [...items]
    const [movedItem] = reordered.splice(fromIndex, 1)
    reordered.splice(toIndex, 0, movedItem)

    handleDragEnd()

    if (onReorder) {
      await onReorder(reordered, fromIndex, toIndex)
    }

    return reordered
  }

  const moveUp = async (items, index) => {
    if (index <= 0 || !items || index >= items.length) return null
    const reordered = [...items]
    const [item] = reordered.splice(index, 1)
    reordered.splice(index - 1, 0, item)

    if (onReorder) {
      await onReorder(reordered, index, index - 1)
    }
    return reordered
  }

  const moveDown = async (items, index) => {
    if (!items || index < 0 || index >= items.length - 1) return null
    const reordered = [...items]
    const [item] = reordered.splice(index, 1)
    reordered.splice(index + 1, 0, item)

    if (onReorder) {
      await onReorder(reordered, index, index + 1)
    }
    return reordered
  }

  return {
    dragIndex,
    dragOverIndex,
    handleDragStart,
    handleDragEnd,
    handleDragOver,
    handleDrop,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    moveUp,
    moveDown
  }
}

export default useDragReorder
